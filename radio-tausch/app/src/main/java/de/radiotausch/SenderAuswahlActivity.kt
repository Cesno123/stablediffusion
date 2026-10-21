package de.radiotausch

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.EditorInfo
import android.widget.ImageView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.widget.doAfterTextChanged
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.progressindicator.LinearProgressIndicator
import com.google.android.material.textfield.TextInputEditText
import java.util.Locale
import java.util.concurrent.Executors

class SenderAuswahlActivity : AppCompatActivity() {

    private val main = Handler(Looper.getMainLooper())
    private val hintergrund = Executors.newSingleThreadExecutor()
    private var anfrageNummer = 0
    private lateinit var laden: LinearProgressIndicator
    private lateinit var hinweis: TextView
    private val liste = SenderListe { gewaehlt ->
        SenderSpeicher.speichere(this, gewaehlt)
        setResult(RESULT_OK)
        finish()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_sender)
        findViewById<MaterialToolbar>(R.id.leiste).setNavigationOnClickListener { finish() }
        laden = findViewById(R.id.laden)
        hinweis = findViewById(R.id.hinweis)
        findViewById<RecyclerView>(R.id.liste).apply {
            layoutManager = LinearLayoutManager(this@SenderAuswahlActivity)
            adapter = liste
        }

        val suche = findViewById<TextInputEditText>(R.id.suche)
        // Erst suchen, wenn man kurz aufhört zu tippen
        val verzoegert = Runnable { lade(suche.text.toString().trim()) }
        suche.doAfterTextChanged {
            main.removeCallbacks(verzoegert)
            main.postDelayed(verzoegert, 500)
        }
        suche.setOnEditorActionListener { _, aktion, _ ->
            if (aktion == EditorInfo.IME_ACTION_SEARCH) {
                main.removeCallbacks(verzoegert)
                verzoegert.run()
                true
            } else false
        }
        lade("")
    }

    // Land des Handys, damit z. B. Franzosen zuerst französische Sender sehen
    private val land = Locale.getDefault().country.ifBlank { "DE" }

    private fun lade(text: String) {
        val nummer = ++anfrageNummer
        laden.visibility = View.VISIBLE
        hintergrund.execute {
            val ergebnis = try {
                if (text.length < 2) SenderSuche.beliebt(land) else SenderSuche.suche(text)
            } catch (e: Exception) {
                null
            }
            main.post {
                if (nummer != anfrageNummer || isFinishing) return@post // veraltete Antwort
                laden.visibility = View.INVISIBLE
                liste.eintraege = ergebnis.orEmpty()
                hinweis.text = when {
                    ergebnis == null -> getString(R.string.no_connection)
                    ergebnis.isEmpty() -> getString(R.string.nothing_found)
                    text.length < 2 -> getString(R.string.popular_in, Locale("", land).displayCountry)
                    else -> getString(R.string.results, ergebnis.size)
                }
            }
        }
    }

    override fun onDestroy() {
        main.removeCallbacksAndMessages(null)
        hintergrund.shutdownNow()
        super.onDestroy()
    }
}

private class SenderListe(private val beiAuswahl: (Sender) -> Unit) : RecyclerView.Adapter<SenderListe.Zeile>() {

    var eintraege: List<Sender> = emptyList()
        set(neu) {
            field = neu
            notifyDataSetChanged()
        }

    class Zeile(view: View) : RecyclerView.ViewHolder(view) {
        val logo: ImageView = view.findViewById(R.id.logo)
        val name: TextView = view.findViewById(R.id.name)
        val info: TextView = view.findViewById(R.id.info)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) =
        Zeile(LayoutInflater.from(parent.context).inflate(R.layout.item_sender, parent, false))

    override fun getItemCount() = eintraege.size

    override fun onBindViewHolder(zeile: Zeile, position: Int) {
        val sender = eintraege[position]
        zeile.name.text = sender.name
        zeile.info.text = sender.info
        LogoLader.zeige(zeile.logo, sender.name, sender.logo)
        zeile.itemView.setOnClickListener { beiAuswahl(sender) }
    }
}
