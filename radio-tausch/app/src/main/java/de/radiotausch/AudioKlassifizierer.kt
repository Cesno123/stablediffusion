package de.radiotausch

import android.content.Context
import android.util.Log
import androidx.annotation.OptIn
import androidx.media3.common.C
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.audio.TeeAudioProcessor
import com.google.mediapipe.tasks.audio.audioclassifier.AudioClassifier
import com.google.mediapipe.tasks.audio.core.RunningMode
import com.google.mediapipe.tasks.components.containers.AudioData
import com.google.mediapipe.tasks.core.BaseOptions
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.TimeUnit

/**
 * Bekommt den Radioton (auch wenn er stumm geschaltet ist) und lässt ihn von der
 * Google-KI "YAMNet" einordnen. Etwa jede Sekunde kommt ein Ergebnis: wie sehr
 * es nach Musik und wie sehr nach Sprache klingt (je 0 bis 1).
 */
@OptIn(UnstableApi::class)
class AudioKlassifizierer(
    context: Context,
    private val ergebnis: (musik: Float, sprache: Float) -> Unit,
) : TeeAudioProcessor.AudioBufferSink {

    private val ki = AudioClassifier.createFromOptions(
        context,
        AudioClassifier.AudioClassifierOptions.builder()
            .setBaseOptions(BaseOptions.builder().setModelAssetPath("yamnet.tflite").build())
            .setRunningMode(RunningMode.AUDIO_CLIPS)
            .setCategoryAllowlist(listOf("Music", "Speech"))
            .build()
    )

    private val warteschlange = LinkedBlockingQueue<FloatArray>(8)
    @Volatile private var laeuft = true

    // Format des Radiotons, wird vom Player gemeldet
    private var abtastrate = 44_100
    private var kanaele = 2
    private var istPcm16 = true

    // Umrechnung auf 16.000 Werte pro Sekunde (das erwartet YAMNet)
    private val fenster = FloatArray(FENSTER)
    private var fuellstand = 0
    private var position = 0.0
    private var summe = 0f
    private var anzahl = 0

    private val arbeiter = Thread {
        while (laeuft) {
            val proben = warteschlange.poll(1, TimeUnit.SECONDS) ?: continue
            try {
                klassifiziere(proben)
            } catch (e: Exception) {
                Log.w("RadioTausch", "Einordnung fehlgeschlagen", e)
            }
        }
        ki.close()
    }.apply { start() }

    override fun flush(sampleRateHz: Int, channelCount: Int, encoding: Int) {
        abtastrate = sampleRateHz
        kanaele = channelCount
        istPcm16 = encoding == C.ENCODING_PCM_16BIT
        fuellstand = 0
        position = 0.0
        summe = 0f
        anzahl = 0
    }

    override fun handleBuffer(buffer: ByteBuffer) {
        if (!istPcm16 || kanaele < 1) return
        val daten = buffer.duplicate().order(ByteOrder.nativeOrder())
        val schritt = abtastrate / ZIELRATE.toDouble()
        val bilder = daten.remaining() / (2 * kanaele)
        repeat(bilder) {
            var mono = 0f
            repeat(kanaele) { mono += daten.short }
            summe += mono / (kanaele * 32768f)
            anzahl++
            position += 1.0
            if (position >= schritt) {
                position -= schritt
                fenster[fuellstand++] = summe / anzahl
                summe = 0f
                anzahl = 0
                if (fuellstand == FENSTER) {
                    warteschlange.offer(fenster.copyOf())
                    fuellstand = 0
                }
            }
        }
    }

    private fun klassifiziere(proben: FloatArray) {
        val format = AudioData.AudioDataFormat.builder()
            .setNumOfChannels(1)
            .setSampleRate(ZIELRATE.toFloat())
            .build()
        val audio = AudioData.create(format, proben.size)
        audio.load(proben)
        var musik = 0f
        var sprache = 0f
        for (teil in ki.classify(audio).classificationResults()) {
            for (kategorie in teil.classifications().flatMap { it.categories() }) {
                when (kategorie.categoryName()) {
                    "Music" -> musik = maxOf(musik, kategorie.score())
                    "Speech" -> sprache = maxOf(sprache, kategorie.score())
                }
            }
        }
        ergebnis(musik, sprache)
    }

    fun beende() {
        laeuft = false
    }

    companion object {
        const val ZIELRATE = 16_000
        const val FENSTER = 15_600 // knapp eine Sekunde
    }
}
