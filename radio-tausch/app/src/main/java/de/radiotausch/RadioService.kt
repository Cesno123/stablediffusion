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
import androidx.annotation.OptIn
import androidx.core.app.ServiceCompat
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.DefaultRenderersFactory
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.audio.AudioSink
import androidx.media3.exoplayer.audio.DefaultAudioSink
import androidx.media3.exoplayer.audio.TeeAudioProcessor

/**
 * Das Herz der App. Das Radio läuft ständig mit, die KI hört zu.
 * - Radio spielt Musik  -> Radio stumm, Spotify spielt ein Lieblingslied.
 * - Spotify-Lied zu Ende -> Spotify pausieren, Radio wieder laut
 *   (läuft im Radio dann immer noch Musik, darf Spotify weiterspielen).
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
        val spotifyText: String = "",
        val meldung: String? = null,
    )

    companion object {
        const val AKTION_STOPP = "de.radiotausch.STOPP"
        @Volatile var status = Status()
        @Volatile var beobachter: ((Status) -> Unit)? = null

        // Wie viele Sekunden am Stück Musik/Sprache, bevor wir es glauben
        private const val SEKUNDEN_BIS_MUSIK = 4
        private const val SEKUNDEN_BIS_SPRACHE = 2
        private const val MUSIK_MINDESTWERT = 0.3f
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
    private var musikFolge = 0
    private var sprachFolge = 0
    private var spotifyStill = 0
    private var spotifySperre = 0
    private var musikWert = 0f
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
        musikFolge = 0
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
            override fun onPlayerError(error: PlaybackException) {
                aktualisiere("Verbindung unterbrochen, neuer Versuch …")
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
        if (musik > MUSIK_MINDESTWERT && musik > sprache) {
            musikFolge++
            sprachFolge = 0
        } else {
            sprachFolge++
            musikFolge = 0
        }
        if (!radioSpieltMusik && musikFolge >= SEKUNDEN_BIS_MUSIK) radioSpieltMusik = true
        if (radioSpieltMusik && sprachFolge >= SEKUNDEN_BIS_SPRACHE) radioSpieltMusik = false

        var meldung: String? = null
        when (modus) {
            Modus.RADIO -> {
                if (spotifySperre > 0) {
                    spotifySperre--
                    meldung = "Spotify hat nicht reagiert – neuer Versuch in $spotifySperre s"
                } else if (radioSpieltMusik) {
                    wechsleZuSpotify()
                }
            }
            Modus.SPOTIFY -> {
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
        aktualisiere(meldung)
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

    private fun aktualisiere(meldung: String? = null) {
        val neu = Status(
            laeuft = !beendet,
            sender = sender?.name.orEmpty(),
            hoertSpotify = modus == Modus.SPOTIFY,
            radioMusik = radioSpieltMusik,
            musik = musikWert,
            sprache = sprachWert,
            spotifyText = spotify?.zustand().orEmpty(),
            meldung = meldung,
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
        val text = if (modus == Modus.SPOTIFY) "Spielt gerade: deine Lieblingssongs"
        else "Spielt gerade: ${sender?.name.orEmpty()}"
        return Notification.Builder(this, "radio")
            .setContentTitle("Radio-Tausch")
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_stat_radio)
            .setColor(getColor(R.color.icon_start))
            .setContentIntent(oeffnen)
            .addAction(Notification.Action.Builder(Icon.createWithResource(this, R.drawable.ic_stop), "Stopp", stopp).build())
            .setOngoing(true)
            .build()
    }

    private fun zeigeHinweis() {
        getSystemService(NotificationManager::class.java).notify(1, baueHinweis())
    }

    private fun alsVordergrundStarten() {
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(NotificationChannel("radio", "Radio-Tausch", NotificationManager.IMPORTANCE_LOW))
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
