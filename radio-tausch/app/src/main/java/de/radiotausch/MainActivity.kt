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
import com.google.android.material.materialswitch.MaterialSwitch
import com.google.android.material.slider.Slider
import com.google.android.material.progressindicator.LinearProgressIndicator

class MainActivity : AppCompatActivity() {

    private lateinit var startStop: MaterialButton
    private lateinit var liveKarte: View
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
        liveKarte = findViewById(R.id.liveKarte)
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
            musikText.text = "Spotify erst nach $s Sekunden Musik im Radio"
        }
        findViewById<Slider>(R.id.musikSekunden).apply {
            value = Einstellungen.musikSekunden(this@MainActivity).toFloat().coerceIn(valueFrom, valueTo)
            zeigeMusikSekunden(value.toInt())
            addOnChangeListener { _, wert, _ ->
                Einstellungen.setzeMusikSekunden(this@MainActivity, wert.toInt())
                zeigeMusikSekunden(wert.toInt())
            }
        }
        findViewById<View>(R.id.spotifyTesten).setOnClickListener { testeSpotify() }
        findViewById<View>(R.id.spotifyOeffnen).setOnClickListener {
            val spotify = packageManager.getLaunchIntentForPackage(SpotifyFernbedienung.SPOTIFY)
            if (spotify != null) startActivity(spotify)
            else Toast.makeText(this, "Spotify ist nicht installiert", Toast.LENGTH_SHORT).show()
        }
    }

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
        val ergebnis = StringBuilder("Vorher: ${fernbedienung.zustandKurz()}\n")
        knopf.isEnabled = false
        ausgabe.visibility = View.VISIBLE

        fun fertig() {
            fernbedienung.pausiere()
            fernbedienung.beende()
            knopf.isEnabled = true
            ausgabe.text = ergebnis.toString() + "\nBitte Screenshot davon an Claude schicken."
        }

        fun teste(weg: Int) {
            if (weg > 2) return fertig()
            ausgabe.text = ergebnis.toString() + "Teste Weg ${weg + 1} von 3 …"
            fernbedienung.pausiere()
            handler.postDelayed({
                if (!fernbedienung.spiele(weg)) {
                    ergebnis.append("Spotify nicht gefunden – Schritt 2 machen.\n")
                    return@postDelayed fertig()
                }
                val start = SystemClock.elapsedRealtime()
                val verlauf = StringBuilder()
                var zuletzt = ""
                handler.post(object : Runnable {
                    override fun run() {
                        val vergangen = SystemClock.elapsedRealtime() - start
                        val zustand = fernbedienung.zustandKurz()
                        if (zustand != zuletzt) {
                            verlauf.append(" %.1fs %s".format(vergangen / 1000.0, zustand))
                            zuletzt = zustand
                        }
                        if (vergangen < 6000) handler.postDelayed(this, 250)
                        else {
                            ergebnis.append("Weg ${weg + 1}:$verlauf\n")
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
            name.text = "Noch kein Sender"
            info.text = "Tippe hier, um einen auszuwählen"
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
            if (erlaubt) "✓ Erlaubt" else "Noch nicht erlaubt – ohne das kann die App Spotify nicht starten."
        findViewById<View>(R.id.zugriffBereich).visibility = if (erlaubt) View.GONE else View.VISIBLE
    }

    private fun zeige(s: RadioService.Status) {
        startStop.text = if (s.laeuft) "Stopp" else "Start"
        startStop.setIconResource(if (s.laeuft) R.drawable.ic_stop else R.drawable.ic_play)
        liveKarte.visibility = if (s.laeuft) View.VISIBLE else View.GONE
        if (!s.laeuft) return

        jetzt.text = s.meldung ?: if (s.hoertSpotify) "🎵 Deine Lieblingssongs" else "📻 ${s.sender}"
        radioGerade.text = if (s.radioMusik) "Im Radio läuft gerade Musik" else "Im Radio wird gerade gesprochen"
        musikBalken.setProgressCompat((s.musik * 100).toInt(), true)
        sprachBalken.setProgressCompat((s.sprache * 100).toInt(), true)
        spotifyStatus.text = s.spotifyText
    }
}
