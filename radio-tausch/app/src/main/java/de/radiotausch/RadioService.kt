package de.radiotausch

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.graphics.drawable.Icon
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import androidx.annotation.OptIn
import androidx.core.app.ServiceCompat
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Metadata
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.DefaultRenderersFactory
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.audio.AudioSink
import androidx.media3.exoplayer.audio.DefaultAudioSink
import androidx.media3.exoplayer.audio.TeeAudioProcessor
import androidx.media3.extractor.metadata.icy.IcyInfo
import java.util.Calendar

/**
 * Das Herz der App. Das Radio läuft ständig mit, die KI hört zu.
 * - Radio spielt Musik  -> Radio stumm, Spotify spielt ein Lieblingslied.
 * - Spotify-Lied zu Ende -> Spotify pausieren, Radio wieder laut
 *   (läuft im Radio dann immer noch Musik, darf Spotify weiterspielen).
 * - Meldet der Sender einen Liedtitel, wird schneller umgeschaltet.
 * - Zu Nachrichtenzeiten bleibt immer das Radio an.
 */
@OptIn(UnstableApi::class)
class RadioService : Service() {

    data class Status(
        val laeuft: Boolean = false,
        val sender: String = "",
        val hoertSpotify: Boolean = false,
        val radioMusik: Boolean = false,
        val musik: Float = 0f,
        val sprache: Float = 0f,
        val spotifyZustand: SpotifyFernbedienung.Zustand = SpotifyFernbedienung.Zustand.WEG,
        val spotifyTitel: String? = null,
        val senderTitel: String? = null,
        val nachrichten: Boolean = false,
        val spotifySperre: Int = 0,
        val verbindungVerloren: Boolean = false,
    )

    companion object {
        const val AKTION_STOPP = "de.radiotausch.STOPP"
        @Volatile var status = Status()
        @Volatile var beobachter: ((Status) -> Unit)? = null

        // Wie viele Sekunden Sprache am Stück, bevor wir es glauben. Etwas Puffer,
        // damit eine kurze Ansage über ein Lied es nicht abbricht.
        // (Für Musik einstellbar in der App, siehe Einstellungen.musikSekunden)
        private const val SEKUNDEN_BIS_SPRACHE = 3
        // Meldet der Sender gerade einen Liedtitel, reicht so viel Musik zur Bestätigung
        private const val SEKUNDEN_MIT_LIEDTITEL = 3
        private const val FRISCHER_TITEL_MS = 30_000L
        // So lange nach der vollen/halben Stunde bleibt das Radio für Nachrichten an
        private const val NACHRICHTEN_SEKUNDEN = 5 * 60
        // Kurz vor der vollen Stunde schon zurück, damit der Anfang nicht fehlt
        private const val NACHRICHTEN_VORLAUF_SEKUNDEN = 15
        // Kommt eins dieser Wörter im Sendertitel vor, laufen Nachrichten/Werbung (mehrsprachig)
        private val NACHRICHTEN_WOERTER = listOf(
            "nachrichten", "news", "wetter", "verkehr", "werbung", "spot",
            "weather", "traffic", "infos", "météo", "noticias", "notizie", "haber",
        )
        // Musik zählt nur, wenn sie klar erkannt wird und deutlich vor Sprache liegt.
        // So zählt Werbung mit Sprecher über Hintergrundmusik nicht als Musik.
        private const val MUSIK_MINDESTWERT = 0.5f
        private const val MUSIK_VORSPRUNG = 0.15f
        // So lange darf Spotify still sein, bevor wir zum Radio zurückgehen
        private const val SPOTIFY_STILL_SEKUNDEN = 10
        // Danach so lange nicht erneut Spotify starten, damit es nicht hin und her springt
        private const val SPOTIFY_SPERRE_SEKUNDEN = 30
    }

    private enum class Modus { RADIO, SPOTIFY }

    private val main = Handler(Looper.getMainLooper())
    private var player: ExoPlayer? = null
    private var klassifizierer: AudioKlassifizierer? = null
    private var spotify: SpotifyFernbedienung? = null
    private var beendet = false

    private var sender: Sender? = null
    private var modus = Modus.RADIO
    private var radioSpieltMusik = false
    // Die letzten Sekunden: true = Musik. Eine einzelne Ausreißer-Sekunde wird toleriert.
    private val verlauf = ArrayDeque<Boolean>()
    private var sprachFolge = 0
    private var spotifyStill = 0
    private var spotifySperre = 0
    private var musikWert = 0f
    // Was der Sender im Stream als "läuft gerade" mitschickt (nicht jeder Sender tut das)
    private var senderTitel: String? = null
    private var senderTitelSeit = 0L
    private var sprachWert = 0f

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == AKTION_STOPP) {
            stopSelf()
            return START_NOT_STICKY
        }
        val gewaehlt = SenderSpeicher.lade(this)
        alsVordergrundStarten()
        when {
            gewaehlt == null -> stopSelf()
            player == null -> {
                sender = gewaehlt
                starte(gewaehlt.url)
            }
            gewaehlt.url != sender?.url -> wechsleSender(gewaehlt)
        }
        return START_NOT_STICKY
    }

    private fun wechsleSender(neu: Sender) {
        sender = neu
        radioSpieltMusik = false
        senderTitel = null
        verlauf.clear()
        sprachFolge = 0
        player?.apply {
            setMediaItem(MediaItem.fromUri(neu.url))
            prepare()
            play()
        }
        zeigeHinweis()
        aktualisiere()
    }

    private fun starte(streamUrl: String) {
        val k = AudioKlassifizierer(this) { musik, sprache ->
            main.post { if (!beendet) beiEinordnung(musik, sprache) }
        }
        klassifizierer = k

        // Zweigt den Radioton für die KI ab, bevor er zum Lautsprecher geht
        val renderer = object : DefaultRenderersFactory(this) {
            override fun buildAudioSink(
                context: Context,
                enableFloatOutput: Boolean,
                enableAudioTrackPlaybackParams: Boolean,
            ): AudioSink = DefaultAudioSink.Builder(context)
                .setAudioProcessors(arrayOf(TeeAudioProcessor(k)))
                .build()
        }

        val p = ExoPlayer.Builder(this, renderer).build()
        p.setWakeMode(C.WAKE_MODE_NETWORK)
        p.addListener(object : Player.Listener {
            override fun onMetadata(metadata: Metadata) {
                for (i in 0 until metadata.length()) {
                    val eintrag = metadata.get(i)
                    if (eintrag is IcyInfo) {
                        val neu = eintrag.title?.trim()?.ifBlank { null }
                        if (neu != senderTitel) senderTitelSeit = SystemClock.elapsedRealtime()
                        senderTitel = neu
                    }
                }
            }

            override fun onPlayerError(error: PlaybackException) {
                aktualisiere(verbindungVerloren = true)
                main.postDelayed({
                    player?.apply {
                        seekToDefaultPosition()
                        prepare()
                        play()
                    }
                }, 3000)
            }
        })
        p.setMediaItem(MediaItem.fromUri(streamUrl))
        p.prepare()
        p.play()
        player = p

        spotify = SpotifyFernbedienung(this, main) { beiLiedwechsel() }
        aktualisiere()
    }

    private fun beiEinordnung(musik: Float, sprache: Float) {
        musikWert = musik
        sprachWert = sprache
        val istMusik = musik >= MUSIK_MINDESTWERT && musik - sprache >= MUSIK_VORSPRUNG
        sprachFolge = if (istMusik) 0 else sprachFolge + 1
        val fenster = if (titelIstLied()) SEKUNDEN_MIT_LIEDTITEL else Einstellungen.musikSekunden(this)
        verlauf.addLast(istMusik)
        while (verlauf.size > fenster) verlauf.removeFirst()
        // Musik erst glauben, wenn das ganze Fenster voll ist und höchstens eine Sekunde abweicht
        if (!radioSpieltMusik && verlauf.size >= fenster && verlauf.count { it } >= fenster - 1) {
            radioSpieltMusik = true
        }
        if (radioSpieltMusik && sprachFolge >= SEKUNDEN_BIS_SPRACHE) radioSpieltMusik = false

        if (nachrichtenZeit()) {
            // Nachrichten haben Vorrang: Spotify pausieren, Radio hören
            if (modus == Modus.SPOTIFY) zurueckZumRadio(spotifyPausieren = true)
            aktualisiere()
            return
        }
        when (modus) {
            Modus.RADIO -> {
                if (spotifySperre > 0) {
                    spotifySperre--
                } else if (radioSpieltMusik) {
                    wechsleZuSpotify()
                }
            }
            Modus.SPOTIFY -> {
                if (!radioSpieltMusik && Einstellungen.sofortZurueck(this)) {
                    zurueckZumRadio(spotifyPausieren = true)
                    aktualisiere()
                    return
                }
                spotify?.pruefe()
                // Sicherheitsnetz: Spielt Spotify länger nicht (manuell pausiert, abgestürzt),
                // zurück zum Radio statt Stille.
                if (spotify?.spieltGerade() == true) {
                    spotifyStill = 0
                } else if (++spotifyStill == 3 || spotifyStill == 6) {
                    // Spotify hat nicht reagiert: Play auf anderem Weg drücken
                    spotify?.spiele(weg = spotifyStill / 3)
                } else if (spotifyStill >= SPOTIFY_STILL_SEKUNDEN) {
                    zurueckZumRadio(spotifyPausieren = true)
                    spotifySperre = SPOTIFY_SPERRE_SEKUNDEN
                }
            }
        }
        aktualisiere()
    }

    /**
     * Hat der Sender gerade frisch einen Liedtitel gemeldet ("Interpret - Titel")?
     * Nur frische Titel zählen: Manche Sender lassen den alten Titel während der Werbung stehen.
     */
    private fun titelIstLied(): Boolean {
        val titel = senderTitel ?: return false
        if (SystemClock.elapsedRealtime() - senderTitelSeit > FRISCHER_TITEL_MS) return false
        val klein = titel.lowercase()
        if (" - " !in titel) return false
        if (NACHRICHTEN_WOERTER.any { it in klein }) return false
        val name = sender?.name?.lowercase().orEmpty()
        return name.isEmpty() || name !in klein
    }

    /** Nachrichtenzeit laut Uhr, oder der Sender meldet selbst Nachrichten/Werbung. */
    private fun nachrichtenZeit(): Boolean {
        val titel = senderTitel?.lowercase()
        if (titel != null && " - " !in titel && NACHRICHTEN_WOERTER.any { it in titel }) return true
        val jetzt = Calendar.getInstance()
        val sekunde = jetzt.get(Calendar.MINUTE) * 60 + jetzt.get(Calendar.SECOND)
        fun um(start: Int) = (sekunde - start + NACHRICHTEN_VORLAUF_SEKUNDEN + 3600) % 3600 <
            NACHRICHTEN_SEKUNDEN + NACHRICHTEN_VORLAUF_SEKUNDEN
        return (Einstellungen.nachrichtenVoll(this) && um(0)) || (Einstellungen.nachrichtenHalb(this) && um(1800))
    }

    private fun wechsleZuSpotify() {
        if (spotify?.spiele() != true) return // Spotify nicht bereit -> Radio läuft einfach weiter
        player?.volume = 0f
        modus = Modus.SPOTIFY
        spotifyStill = 0
        zeigeHinweis()
    }

    private fun beiLiedwechsel() {
        if (modus != Modus.SPOTIFY) return
        if (radioSpieltMusik) return // im Radio läuft noch Musik: nächstes Spotify-Lied darf laufen
        zurueckZumRadio(spotifyPausieren = true)
    }

    private fun zurueckZumRadio(spotifyPausieren: Boolean) {
        if (spotifyPausieren) spotify?.pausiere()
        player?.volume = 1f
        modus = Modus.RADIO
        zeigeHinweis()
        aktualisiere()
    }

    private fun aktualisiere(verbindungVerloren: Boolean = false) {
        val neu = Status(
            laeuft = !beendet,
            sender = sender?.name.orEmpty(),
            hoertSpotify = modus == Modus.SPOTIFY,
            radioMusik = radioSpieltMusik,
            musik = musikWert,
            sprache = sprachWert,
            spotifyZustand = spotify?.zustandFuerAnzeige() ?: SpotifyFernbedienung.Zustand.WEG,
            spotifyTitel = spotify?.aktuellerTitel(),
            senderTitel = senderTitel,
            nachrichten = nachrichtenZeit(),
            spotifySperre = if (modus == Modus.RADIO) spotifySperre else 0,
            verbindungVerloren = verbindungVerloren,
        )
        status = neu
        beobachter?.invoke(neu)
    }

    private fun baueHinweis(): Notification {
        val oeffnen = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE
        )
        val stopp = PendingIntent.getService(
            this, 1, Intent(this, RadioService::class.java).setAction(AKTION_STOPP), PendingIntent.FLAG_IMMUTABLE
        )
        val texte = inAppSprache()
        val text = if (modus == Modus.SPOTIFY) texte.getString(R.string.notif_spotify)
        else texte.getString(R.string.notif_radio, sender?.name.orEmpty())
        return Notification.Builder(this, "radio")
            .setContentTitle(texte.getString(R.string.app_name))
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_stat_radio)
            .setColor(getColor(R.color.icon_start))
            .setContentIntent(oeffnen)
            .addAction(Notification.Action.Builder(Icon.createWithResource(this, R.drawable.ic_stop), texte.getString(R.string.stop), stopp).build())
            .setOngoing(true)
            .build()
    }

    private fun zeigeHinweis() {
        getSystemService(NotificationManager::class.java).notify(1, baueHinweis())
    }

    private fun alsVordergrundStarten() {
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(NotificationChannel("radio", getString(R.string.app_name), NotificationManager.IMPORTANCE_LOW))
        val typ = if (Build.VERSION.SDK_INT >= 29) ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK else 0
        ServiceCompat.startForeground(this, 1, baueHinweis(), typ)
    }

    override fun onDestroy() {
        beendet = true
        main.removeCallbacksAndMessages(null)
        player?.release()
        player = null
        klassifizierer?.beende()
        spotify?.beende()
        status = Status()
        beobachter?.invoke(status)
        super.onDestroy()
    }
}
