package de.radiotausch

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.provider.Settings
import android.view.View
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.NotificationManagerCompat
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.materialswitch.MaterialSwitch
import com.google.android.material.slider.Slider
import com.google.android.material.progressindicator.LinearProgressIndicator

class MainActivity : AppCompatActivity() {

    private lateinit var startStop: MaterialButton
    private lateinit var jetzt: TextView
    private lateinit var radioGerade: TextView
    private lateinit var musikBalken: LinearProgressIndicator
    private lateinit var sprachBalken: LinearProgressIndicator
    private lateinit var spotifyStatus: TextView

    private val senderWahl = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { ergebnis ->
        zeigeSender()
        // Läuft die App schon, gleich auf den neuen Sender umschalten
        if (ergebnis.resultCode == RESULT_OK && RadioService.status.laeuft) starteDienst()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        startStop = findViewById(R.id.startStop)
        jetzt = findViewById(R.id.jetzt)
        radioGerade = findViewById(R.id.radioGerade)
        musikBalken = findViewById(R.id.musikBalken)
        sprachBalken = findViewById(R.id.sprachBalken)
        spotifyStatus = findViewById(R.id.spotifyStatus)

        val waehlen = View.OnClickListener { senderWahl.launch(Intent(this, SenderAuswahlActivity::class.java)) }
        findViewById<View>(R.id.senderKarte).setOnClickListener(waehlen)
        findViewById<View>(R.id.senderAendern).setOnClickListener(waehlen)

        startStop.setOnClickListener {
            when {
                RadioService.status.laeuft -> stopService(Intent(this, RadioService::class.java))
                SenderSpeicher.lade(this) == null -> waehlen.onClick(it)
                else -> starteDienst()
            }
        }
        findViewById<View>(R.id.zugriff).setOnClickListener {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        }
        findViewById<View>(R.id.appInfo).setOnClickListener {
            startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:$packageName")))
        }
        findViewById<MaterialSwitch>(R.id.sofortZurueck).apply {
            isChecked = Einstellungen.sofortZurueck(this@MainActivity)
            setOnCheckedChangeListener { _, an -> Einstellungen.setzeSofortZurueck(this@MainActivity, an) }
        }
        val musikText = findViewById<TextView>(R.id.musikSekundenText)
        fun zeigeMusikSekunden(s: Int) {
            musikText.text = getString(R.string.music_seconds, s)
        }
        findViewById<Slider>(R.id.musikSekunden).apply {
            value = Einstellungen.musikSekunden(this@MainActivity).toFloat().coerceIn(valueFrom, valueTo)
            zeigeMusikSekunden(value.toInt())
            addOnChangeListener { _, wert, _ ->
                Einstellungen.setzeMusikSekunden(this@MainActivity, wert.toInt())
                zeigeMusikSekunden(wert.toInt())
            }
        }
        findViewById<MaterialSwitch>(R.id.nachrichtenVoll).apply {
            isChecked = Einstellungen.nachrichtenVoll(this@MainActivity)
            setOnCheckedChangeListener { _, an -> Einstellungen.setzeNachrichtenVoll(this@MainActivity, an) }
        }
        findViewById<MaterialSwitch>(R.id.nachrichtenHalb).apply {
            isChecked = Einstellungen.nachrichtenHalb(this@MainActivity)
            setOnCheckedChangeListener { _, an -> Einstellungen.setzeNachrichtenHalb(this@MainActivity, an) }
        }
        findViewById<View>(R.id.spotifyTesten).setOnClickListener { testeSpotify() }
        findViewById<View>(R.id.spotifyOeffnen).setOnClickListener {
            val spotify = packageManager.getLaunchIntentForPackage(SpotifyFernbedienung.SPOTIFY)
            if (spotify != null) startActivity(spotify)
            else Toast.makeText(this, R.string.spotify_not_installed, Toast.LENGTH_SHORT).show()
        }
        zeigeSprache()
        findViewById<View>(R.id.spracheKarte).setOnClickListener { waehleSprache() }
    }

    private fun sprachName(kuerzel: String) =
        Sprache.auswahl.firstOrNull { it.first == kuerzel }?.second ?: getString(R.string.language_system)

    private fun zeigeSprache() {
        findViewById<TextView>(R.id.spracheAktuell).text = sprachName(Sprache.aktuell())
    }

    private fun waehleSprache() {
        val namen = Sprache.auswahl.map { sprachName(it.first) }.toTypedArray()
        val gewaehlt = Sprache.auswahl.indexOfFirst { it.first == Sprache.aktuell() }.coerceAtLeast(0)
        MaterialAlertDialogBuilder(this)
            .setTitle(R.string.language_title)
            .setSingleChoiceItems(namen, gewaehlt) { dialog, i ->
                dialog.dismiss()
                Sprache.setze(Sprache.auswahl[i].first) // baut den Bildschirm in der neuen Sprache neu auf
            }
            .show()
    }

    private fun zustandText(z: SpotifyFernbedienung.Zustand) = getString(
        when (z) {
            SpotifyFernbedienung.Zustand.SPIELT -> R.string.state_playing
            SpotifyFernbedienung.Zustand.PAUSIERT -> R.string.state_paused
            SpotifyFernbedienung.Zustand.GESTOPPT -> R.string.state_stopped
            SpotifyFernbedienung.Zustand.LAEDT -> R.string.state_loading
            SpotifyFernbedienung.Zustand.LEER -> R.string.state_empty
            SpotifyFernbedienung.Zustand.WEG -> R.string.state_gone
        }
    )

    /**
     * Probiert alle drei Play-Wege nacheinander aus und schreibt auf, was Spotify jeweils
     * in den nächsten 6 Sekunden macht. So sehen wir, welcher Weg auf diesem Handy funktioniert.
     */
    private fun testeSpotify() {
        val ausgabe = findViewById<TextView>(R.id.testErgebnis)
        val knopf = findViewById<View>(R.id.spotifyTesten)
        if (RadioService.status.laeuft) stopService(Intent(this, RadioService::class.java))
        val handler = Handler(Looper.getMainLooper())
        val fernbedienung = SpotifyFernbedienung(this, handler) {}
        val ergebnis = StringBuilder(getString(R.string.test_before, zustandText(fernbedienung.zustand())) + "\n")
        knopf.isEnabled = false
        ausgabe.visibility = View.VISIBLE

        fun fertig() {
            fernbedienung.pausiere()
            fernbedienung.beende()
            knopf.isEnabled = true
            ausgabe.text = ergebnis.toString() + "\n" + getString(R.string.test_done)
        }

        fun teste(weg: Int) {
            if (weg > 2) return fertig()
            ausgabe.text = ergebnis.toString() + getString(R.string.test_running, weg + 1)
            fernbedienung.pausiere()
            handler.postDelayed({
                if (!fernbedienung.spiele(weg)) {
                    ergebnis.append(getString(R.string.test_not_found)).append("\n")
                    return@postDelayed fertig()
                }
                val start = SystemClock.elapsedRealtime()
                val verlauf = StringBuilder()
                var zuletzt = ""
                handler.post(object : Runnable {
                    override fun run() {
                        val vergangen = SystemClock.elapsedRealtime() - start
                        val zustand = zustandText(fernbedienung.zustand())
                        if (zustand != zuletzt) {
                            verlauf.append(" %.1fs %s".format(vergangen / 1000.0, zustand))
                            zuletzt = zustand
                        }
                        if (vergangen < 6000) handler.postDelayed(this, 250)
                        else {
                            ergebnis.append(getString(R.string.test_method, weg + 1, verlauf)).append("\n")
                            teste(weg + 1)
                        }
                    }
                })
            }, 2000)
        }
        teste(0)
    }

    override fun onResume() {
        super.onResume()
        zeigeSender()
        zeigeZugriff()
        RadioService.beobachter = { s -> runOnUiThread { zeige(s) } }
        zeige(RadioService.status)
    }

    override fun onPause() {
        RadioService.beobachter = null
        super.onPause()
    }

    private fun starteDienst() {
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }
        startForegroundService(Intent(this, RadioService::class.java))
    }

    private fun zeigeSender() {
        val sender = SenderSpeicher.lade(this)
        val name = findViewById<TextView>(R.id.senderName)
        val info = findViewById<TextView>(R.id.senderInfo)
        val logo = findViewById<ImageView>(R.id.senderLogo)
        if (sender == null) {
            name.setText(R.string.no_station)
            info.setText(R.string.no_station_hint)
            LogoLader.zeige(logo, "?", "")
        } else {
            name.text = sender.name
            info.text = sender.info
            LogoLader.zeige(logo, sender.name, sender.logo)
        }
    }

    private fun zeigeZugriff() {
        val erlaubt = NotificationManagerCompat.getEnabledListenerPackages(this).contains(packageName)
        findViewById<TextView>(R.id.zugriffStatus).text =
            getString(if (erlaubt) R.string.allowed else R.string.not_allowed)
        findViewById<View>(R.id.zugriffBereich).visibility = if (erlaubt) View.GONE else View.VISIBLE
    }

    private fun zeige(s: RadioService.Status) {
        startStop.setText(if (s.laeuft) R.string.stop else R.string.start)
        startStop.setIconResource(if (s.laeuft) R.drawable.ic_stop else R.drawable.ic_play)
        if (!s.laeuft) {
            // Karte bleibt sichtbar, damit man sie kennt, auch wenn gerade nichts läuft
            jetzt.setText(R.string.ready)
            radioGerade.setText(R.string.tap_start)
            musikBalken.setProgressCompat(0, true)
            sprachBalken.setProgressCompat(0, true)
            spotifyStatus.text = ""
            return
        }

        jetzt.text = when {
            s.verbindungVerloren -> getString(R.string.connection_lost)
            s.spotifySperre > 0 -> getString(R.string.spotify_blocked, s.spotifySperre)
            s.hoertSpotify -> getString(R.string.now_spotify)
            s.nachrichten -> getString(R.string.now_news, s.sender)
            else -> getString(R.string.now_radio, s.sender)
        }
        radioGerade.setText(if (s.radioMusik) R.string.radio_music else R.string.radio_talk)
        musikBalken.setProgressCompat((s.musik * 100).toInt(), true)
        sprachBalken.setProgressCompat((s.sprache * 100).toInt(), true)
        val senderZeile = s.senderTitel?.let { getString(R.string.station_reports, it) }
            ?: getString(R.string.station_reports_nothing)
        val titel = s.spotifyTitel?.let { " – $it" }.orEmpty()
        val spotifyZeile = when (s.spotifyZustand) {
            SpotifyFernbedienung.Zustand.SPIELT -> getString(R.string.spotify_playing, titel)
            SpotifyFernbedienung.Zustand.WEG -> getString(R.string.spotify_missing)
            else -> getString(R.string.spotify_paused, titel)
        }
        spotifyStatus.text = "$senderZeile\n$spotifyZeile"
    }
}
