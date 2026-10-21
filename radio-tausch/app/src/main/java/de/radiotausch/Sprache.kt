package de.radiotausch

import android.content.Context
import android.content.res.Configuration
import android.os.LocaleList
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat

/** Sprache der App, unabhängig von der Handy-Sprache wählbar. */
object Sprache {
    /** Kürzel und Name in der jeweiligen Sprache selbst. Leeres Kürzel = wie das Handy. */
    val auswahl = listOf(
        "" to null,
        "en" to "English",
        "de" to "Deutsch",
        "fr" to "Français",
        "es" to "Español",
        "it" to "Italiano",
        "tr" to "Türkçe",
    )

    fun aktuell(): String = AppCompatDelegate.getApplicationLocales()[0]?.language.orEmpty()

    fun setze(kuerzel: String) {
        AppCompatDelegate.setApplicationLocales(
            if (kuerzel.isEmpty()) LocaleListCompat.getEmptyLocaleList()
            else LocaleListCompat.forLanguageTags(kuerzel)
        )
    }
}

/**
 * Für Dienste: Vor Android 13 gilt die gewählte App-Sprache nur in Bildschirmen,
 * deshalb hier für Benachrichtigungstexte selbst anwenden.
 */
fun Context.inAppSprache(): Context {
    val sprachen = AppCompatDelegate.getApplicationLocales()
    if (sprachen.isEmpty) return this
    val konfiguration = Configuration(resources.configuration)
    konfiguration.setLocales(LocaleList.forLanguageTags(sprachen.toLanguageTags()))
    return createConfigurationContext(konfiguration)
}
