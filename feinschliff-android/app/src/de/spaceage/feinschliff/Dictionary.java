package de.spaceage.feinschliff;

import android.content.Context;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Word list for suggestions and autocorrect: assets/dict.tsv (sorted "key TAB display TAB zipf*100")
 * plus the words this phone has learned (files/user_words.tsv, never leaves the device).
 * Nothing is censored; every word in the list can be suggested.
 */
final class Dictionary {
    private static final String ALPHABET = "abcdefghijklmnopqrstuvwxyzäöüß";
    private static final String[] ROWS = {"qwertzuiopü", "asdfghjklöä", "yxcvbnm"};
    private static final float[] ROW_OFFSET = {0f, 0.25f, 0.75f};
    static final int KNOWN = 2;                 // a new word counts as known after two uses
    private static final int MAX_USER = 5000;

    private final String[] keys, shown;         // shown[i] == null: display form equals the key
    private final short[] freq;
    private final Map<String, int[]> user = new HashMap<>();     // key -> {count}
    private final Map<String, String> userShown = new HashMap<>();
    private final File userFile;
    private boolean dirty;

    static final class Suggestion {
        final String key, word;
        final int score;
        final boolean correction;
        Suggestion(String key, String word, int score, boolean correction) {
            this.key = key; this.word = word; this.score = score; this.correction = correction;
        }
    }

    static String key(String word) { return word.toLowerCase(Locale.GERMAN); }

    /** Loads both lists; slow (a few hundred ms), so call it off the main thread. */
    Dictionary(Context ctx) throws Exception {
        ArrayList<String> k = new ArrayList<>(100000), s = new ArrayList<>(100000);
        ArrayList<Short> f = new ArrayList<>(100000);
        try (BufferedReader r = new BufferedReader(new InputStreamReader(ctx.getAssets().open("dict.tsv"), "UTF-8"), 1 << 16)) {
            String line;
            while ((line = r.readLine()) != null) {
                int a = line.indexOf('\t'), b = line.indexOf('\t', a + 1);
                if (a <= 0 || b <= a) continue;
                String key = line.substring(0, a), disp = line.substring(a + 1, b);
                k.add(key);
                s.add(disp.equals(key) ? null : disp);
                f.add((short) Integer.parseInt(line.substring(b + 1)));
            }
        }
        keys = k.toArray(new String[0]);
        shown = s.toArray(new String[0]);
        freq = new short[f.size()];
        for (int i = 0; i < freq.length; i++) freq[i] = f.get(i);

        userFile = new File(ctx.getFilesDir(), "user_words.tsv");
        if (userFile.exists()) {
            try (BufferedReader r = new BufferedReader(new InputStreamReader(new FileInputStream(userFile), "UTF-8"))) {
                String line;
                while ((line = r.readLine()) != null) {
                    String[] p = line.split("\t");
                    if (p.length < 2) continue;
                    user.put(key(p[0]), new int[]{Integer.parseInt(p[1])});
                    userShown.put(key(p[0]), p[0]);
                }
            } catch (Exception ignored) { }
        }
    }

    private int find(String key) { return Arrays.binarySearch(keys, key); }

    private int userCount(String key) { int[] c = user.get(key); return c == null ? 0 : c[0]; }

    /** In the word list, or typed often enough on this phone. */
    boolean isKnown(String word) {
        String k = key(word);
        return find(k) >= 0 || userCount(k) >= KNOWN;
    }

    /** The dictionary's spelling of a known word (Haus for haus), or null. */
    String displayOf(String word) {
        String k = key(word);
        int i = find(k);
        if (i >= 0) return shown[i] != null ? shown[i] : k;
        return userCount(k) >= KNOWN ? userShown.get(k) : null;
    }

    private int score(int i) { return freq[i] + boost(keys[i]); }

    private int boost(String key) { return Math.min(userCount(key) * 15, 150); }

    // --- learning

    /** A finished word: counts towards learning new words and ranks familiar ones higher. */
    void used(String word) {
        if (word.length() < 2 || word.length() > 40) return;
        String k = key(word);
        int[] c = user.get(k);
        if (c == null) {
            // common words only get a ranking boost while there is room; new words always keep 1000 places
            if (user.size() >= MAX_USER || (find(k) >= 0 && user.size() >= MAX_USER - 1000)) return;
            user.put(k, c = new int[]{0});
            userShown.put(k, word);
        }
        c[0]++;
        String old = userShown.get(k);
        if (old != null && !old.equals(word) && word.equals(k) && find(k) < 0) userShown.put(k, word);   // new word seen in lower case too
        dirty = true;
    }

    /** The user insisted on this spelling (undid an autocorrect, tapped the literal word). */
    void learn(String word) {
        String k = key(word);
        int[] c = user.get(k);
        if (c == null) { user.put(k, new int[]{KNOWN}); userShown.put(k, word); }
        else c[0] = Math.max(c[0], KNOWN);
        userShown.put(k, word);
        dirty = true;
    }

    /** Writes the learned words in the background. */
    void save() {
        if (!dirty) return;
        dirty = false;
        final StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, int[]> e : user.entrySet()) {
            String w = userShown.get(e.getKey());
            sb.append(w != null ? w : e.getKey()).append('\t').append(e.getValue()[0]).append('\n');
        }
        new Thread(new Runnable() {
            public void run() {
                File tmp = new File(userFile.getPath() + ".tmp");
                try (Writer w = new OutputStreamWriter(new FileOutputStream(tmp), "UTF-8")) {
                    w.write(sb.toString());
                } catch (Exception e) { return; }
                tmp.renameTo(userFile);
            }
        }).start();
    }

    // --- suggestions

    private static float[] pos(char c) {
        for (int r = 0; r < ROWS.length; r++) {
            int i = ROWS[r].indexOf(c);
            if (i >= 0) return new float[]{i + ROW_OFFSET[r], r};
        }
        return null;
    }

    /** Typo bonus: the wrong letter sits next to the right one, or is the same letter without umlaut. */
    private static int near(char typed, char meant) {
        if ((typed == 'a' && meant == 'ä') || (typed == 'o' && meant == 'ö') || (typed == 'u' && meant == 'ü')
                || (typed == 's' && meant == 'ß')) return 70;
        float[] a = pos(typed), b = pos(meant);
        if (a == null || b == null) return 0;
        return Math.abs(a[1] - b[1]) <= 1 && Math.abs(a[0] - b[0]) <= 1.1f ? 50 : 0;
    }

    private void addCandidate(Map<String, Suggestion> out, String k, int extra, boolean correction) {
        int i = find(k);
        int s;
        String disp;
        if (i >= 0) { s = score(i) + extra; disp = shown[i] != null ? shown[i] : k; }
        else if (userCount(k) >= KNOWN) { s = 350 + boost(k) + extra; disp = userShown.get(k); }
        else return;
        Suggestion old = out.get(k);
        if (old == null || old.score < s) out.put(k, new Suggestion(k, disp, s, correction));
    }

    /** Spelling corrections one typo away (wrong, missing, extra or swapped letter; ss for ß). */
    private void corrections(String w, Map<String, Suggestion> out) {
        int n = w.length();
        char[] c = w.toCharArray();
        for (int i = 0; i < n; i++) {
            addCandidate(out, w.substring(0, i) + w.substring(i + 1), -130, true);                  // extra letter
            if (i + 1 < n && c[i] != c[i + 1])
                addCandidate(out, w.substring(0, i) + c[i + 1] + c[i] + w.substring(i + 2), -100, true);  // swapped
            for (int a = 0; a < ALPHABET.length(); a++) {
                char x = ALPHABET.charAt(a);
                if (x != c[i]) addCandidate(out, w.substring(0, i) + x + w.substring(i + 1), -140 + near(c[i], x), true);
            }
        }
        for (int i = 0; i <= n; i++)
            for (int a = 0; a < ALPHABET.length(); a++)
                addCandidate(out, w.substring(0, i) + ALPHABET.charAt(a) + w.substring(i), -140, true);  // missing
        for (int i = w.indexOf("ss"); i >= 0; i = w.indexOf("ss", i + 1))
            addCandidate(out, w.substring(0, i) + "ß" + w.substring(i + 2), -40, true);
    }

    /** Words starting with the typed letters, best first. */
    private void completions(String w, Map<String, Suggestion> out) {
        for (int i : w.length() == 1 ? firstLetter(w) : prefixRange(w)) {
            int s = score(i) - (keys[i].length() - w.length()) * 8;
            if (keys[i].equals(w)) s += 120;
            Suggestion old = out.get(keys[i]);
            if (old == null || old.score < s) out.put(keys[i], new Suggestion(keys[i], shown[i] != null ? shown[i] : keys[i], s, false));
        }
        for (Map.Entry<String, int[]> e : user.entrySet())
            if (e.getValue()[0] >= KNOWN && e.getKey().startsWith(w) && find(e.getKey()) < 0) {
                int s = 350 + boost(e.getKey()) + (e.getKey().equals(w) ? 120 : 0);
                out.put(e.getKey(), new Suggestion(e.getKey(), userShown.get(e.getKey()), s, false));
            }
    }

    private int[] prefixRange(String w) {
        int from = find(w);
        if (from < 0) from = -from - 1;
        int to = from;
        while (to < keys.length && keys[to].startsWith(w)) to++;
        int[] r = new int[to - from];
        for (int i = 0; i < r.length; i++) r[i] = from + i;
        return r;
    }

    private final Map<String, int[]> firstLetterCache = new HashMap<>();

    /** One letter matches thousands of words; the 60 most common are plenty and computed once. */
    private int[] firstLetter(String w) {
        int[] top = firstLetterCache.get(w);
        if (top != null) return top;
        final int[] all = prefixRange(w);
        Integer[] idx = new Integer[all.length];
        for (int i = 0; i < all.length; i++) idx[i] = all[i];
        Arrays.sort(idx, new java.util.Comparator<Integer>() {
            public int compare(Integer a, Integer b) { return freq[b] - freq[a]; }
        });
        top = new int[Math.min(60, idx.length)];
        for (int i = 0; i < top.length; i++) top[i] = idx[i];
        firstLetterCache.put(w, top);
        return top;
    }

    /** Best matches for a word being typed: completions, and corrections if it may be misspelled. */
    List<Suggestion> suggest(String typed, int max) {
        String w = key(typed);
        Map<String, Suggestion> out = new HashMap<>();
        completions(w, out);
        if (w.length() >= 2) corrections(w, out);
        List<Suggestion> list = new ArrayList<>(out.values());
        java.util.Collections.sort(list, new java.util.Comparator<Suggestion>() {
            public int compare(Suggestion a, Suggestion b) { return b.score - a.score; }
        });
        return list.size() > max ? new ArrayList<>(list.subList(0, max)) : list;
    }

    /**
     * What a finished word should become, or null to leave it alone. Careful on purpose: only
     * unknown words with one clear, common correction, plus the capital letter of known nouns.
     */
    String autocorrect(String typed) {
        if (typed.length() < 2) return null;
        for (int i = 0; i < typed.length(); i++) if (!Character.isLetter(typed.charAt(i))) return null;
        if (typed.length() > 1 && typed.equals(typed.toUpperCase(Locale.GERMAN))) return null;   // ABC
        String disp = displayOf(typed);
        if (disp != null && userCount(key(typed)) >= KNOWN && typed.equals(userShown.get(key(typed))))
            return null;                                              // spelled exactly as the user taught it
        if (disp != null) {
            boolean lowerTyped = typed.equals(key(typed));
            return lowerTyped && !disp.equals(typed) && disp.length() == typed.length() && typed.length() >= 3
                    && Character.isUpperCase(disp.charAt(0)) && key(disp).equals(typed) ? disp : null;
        }
        if (typed.length() < 3) return null;
        Map<String, Suggestion> out = new HashMap<>();
        corrections(key(typed), out);
        Suggestion best = null, second = null;
        for (Suggestion s : out.values()) {
            if (best == null || s.score > best.score) { second = best; best = s; }
            else if (second == null || s.score > second.score) second = s;
        }
        if (best == null || best.score < 230) return null;          // too rare to be a safe guess
        if (second != null && best.score - second.score < 50) return null;   // two plausible fixes: don't guess
        return best.word;
    }
}
