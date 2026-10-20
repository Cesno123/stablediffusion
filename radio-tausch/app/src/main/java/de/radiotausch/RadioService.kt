package de.radiotausch

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
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

    companion object {
        const val EXTRA_SENDER = "sender"
        @Volatile var statusAnzeige: ((String) -> Unit)? = null
        @Volatile var letzterStatus = "Gestoppt"

        // Wie viele Sekunden am Stück Musik/Sprache, bevor wir es glauben
        private const val SEKUNDEN_BIS_MUSIK = 4
        private const val SEKUNDEN_BIS_SPRACHE = 2
        private const val MUSIK_MINDESTWERT = 0.3f
    }

    private enum class Modus { RADIO, SPOTIFY }

    private val main = Handler(Looper.getMainLooper())
    private var player: ExoPlayer? = null
    private var klassifizierer: AudioKlassifizierer? = null
    private var spotify: SpotifyFernbedienung? = null
    private var beendet = false

    private var senderName = ""
    private var modus = Modus.RADIO
    private var radioSpieltMusik = false
    private var musikFolge = 0
    private var sprachFolge = 0
    private var spotifyStill = 0
    private var musikWert = 0f
    private var sprachWert = 0f

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        alsVordergrundStarten()
        if (player == null) {
            val name = intent?.getStringExtra(EXTRA_SENDER)?.trim()?.ifBlank { null } ?: "Radio Köln"
            melde("Suche Sender „$name“ …")
            Thread {
                val sender = try {
                    SenderSuche.finde(name)
                } catch (e: Exception) {
                    null
                }
                main.post {
                    if (beendet) return@post
                    if (sender == null) {
                        melde("Sender „$name“ nicht gefunden.\nInternet prüfen oder den Namen anders schreiben.")
                    } else {
                        senderName = sender.name
                        starte(sender.url)
                    }
                }
            }.start()
        }
        return START_NOT_STICKY
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
                melde("Radio-Verbindung unterbrochen, neuer Versuch …")
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
        zeigeStatus()
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

        when (modus) {
            Modus.RADIO -> if (radioSpieltMusik) wechsleZuSpotify()
            Modus.SPOTIFY -> {
                // Sicherheitsnetz: Spielt Spotify nicht (manuell pausiert, abgestürzt),
                // nach ein paar Sekunden zurück zum Radio statt Stille.
                if (spotify?.spieltGerade() == true) spotifyStill = 0
                else if (++spotifyStill >= 6) zurueckZumRadio(spotifyPausieren = false)
            }
        }
        zeigeStatus()
    }

    private fun wechsleZuSpotify() {
        if (spotify?.spiele() != true) return // Spotify nicht bereit -> Radio läuft einfach weiter
        player?.volume = 0f
        modus = Modus.SPOTIFY
        spotifyStill = 0
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
        zeigeStatus()
    }

    private fun zeigeStatus() {
        val jetzt = if (modus == Modus.SPOTIFY) "Du hörst: Spotify" else "Du hörst: $senderName"
        val radio = if (radioSpieltMusik) "Musik" else "Moderation / Nachrichten"
        val sp = if (spotify?.verfuegbar() == true) "Spotify: verbunden ✓"
        else "Spotify: nicht gefunden – Spotify öffnen, Lieblingssongs (Zufall) starten und pausieren"
        melde("$jetzt\n\nIm Radio gerade: $radio\n(Musik ${prozent(musikWert)} %, Sprache ${prozent(sprachWert)} %)\n\n$sp")
    }

    private fun prozent(wert: Float) = (wert * 100).toInt()

    private fun melde(text: String) {
        letzterStatus = text
        statusAnzeige?.invoke(text)
    }

    private fun alsVordergrundStarten() {
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(NotificationChannel("radio", "Radio-Tausch", NotificationManager.IMPORTANCE_LOW))
        val oeffnen = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE
        )
        val hinweis = Notification.Builder(this, "radio")
            .setContentTitle("Radio-Tausch läuft")
            .setSmallIcon(android.R.drawable.ic_media_play)
            .setContentIntent(oeffnen)
            .setOngoing(true)
            .build()
        val typ = if (Build.VERSION.SDK_INT >= 29) ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK else 0
        ServiceCompat.startForeground(this, 1, hinweis, typ)
    }

    override fun onDestroy() {
        beendet = true
        main.removeCallbacksAndMessages(null)
        player?.release()
        player = null
        klassifizierer?.beende()
        spotify?.beende()
        melde("Gestoppt")
        super.onDestroy()
    }
}
