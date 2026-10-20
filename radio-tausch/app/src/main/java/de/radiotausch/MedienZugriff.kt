package de.radiotausch

import android.service.notification.NotificationListenerService

/**
 * Leerer Dienst. Android erlaubt einer App nur dann, andere Player (Spotify)
 * zu steuern, wenn der Nutzer ihr den "Benachrichtigungszugriff" gegeben hat.
 */
class MedienZugriff : NotificationListenerService()
