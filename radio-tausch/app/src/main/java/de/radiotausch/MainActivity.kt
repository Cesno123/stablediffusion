package de.radiotausch

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.core.app.NotificationManagerCompat

class MainActivity : Activity() {

    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        status = findViewById(R.id.status)
        val sender = findViewById<EditText>(R.id.sender)

        findViewById<Button>(R.id.zugriff).setOnClickListener {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        }
        findViewById<Button>(R.id.start).setOnClickListener {
            if (Build.VERSION.SDK_INT >= 33 &&
                checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
            ) {
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
            }
            val start = Intent(this, RadioService::class.java)
                .putExtra(RadioService.EXTRA_SENDER, sender.text.toString())
            startForegroundService(start)
        }
        findViewById<Button>(R.id.stop).setOnClickListener {
            stopService(Intent(this, RadioService::class.java))
        }
    }

    override fun onResume() {
        super.onResume()
        RadioService.statusAnzeige = { text -> runOnUiThread { zeige(text) } }
        zeige(RadioService.letzterStatus)
    }

    override fun onPause() {
        RadioService.statusAnzeige = null
        super.onPause()
    }

    private fun zeige(text: String) {
        val zugriff = NotificationManagerCompat.getEnabledListenerPackages(this).contains(packageName)
        status.text = if (zugriff) text else "⚠ Schritt 1 fehlt: „Zugriff erlauben“ tippen.\n\n$text"
    }
}
