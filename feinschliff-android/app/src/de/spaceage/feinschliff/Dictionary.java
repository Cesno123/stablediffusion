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
    private final java.util.BitSet doubtful;    // swipe typing ranks these down
    private final Map<String, int[]> user = new HashMap<>();     // key -> {count}
    private final Map<String, String> userShown = new HashMap<>();
    private final File userFile, pairFile;
    private final Map<String, int[]> pairs = new HashMap<>();     // "prev word" -> how often typed in a row here
    private String ctxPrev;
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
        ArrayList<Integer> odd = new ArrayList<>();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(ctx.getAssets().open("dict.tsv"), "UTF-8"), 1 << 16)) {
            String line;
            while ((line = r.readLine()) != null) {
                int a = line.indexOf('\t'), b = line.indexOf('\t', a + 1);
                if (a <= 0 || b <= a) continue;
                int c = line.indexOf('\t', b + 1);
                String key = line.substring(0, a), disp = line.substring(a + 1, b);
                if (c > 0) odd.add(k.size());           // "x": English or an odd short token
                k.add(key);
                s.add(disp.equals(key) ? null : disp);
                f.add((short) Integer.parseInt(c > 0 ? line.substring(b + 1, c) : line.substring(b + 1)));
            }
        }
        keys = k.toArray(new String[0]);
        shown = s.toArray(new String[0]);
        freq = new short[f.size()];
        for (int i = 0; i < freq.length; i++) freq[i] = f.get(i);
        doubtful = new java.util.BitSet(keys.length);
        for (int i : odd) doubtful.set(i);

        try (BufferedReader r = new BufferedReader(new InputStreamReader(ctx.getAssets().open("bigrams.tsv"), "UTF-8"), 1 << 16)) {
            String line;
            while ((line = r.readLine()) != null) {
                int tab = line.indexOf('\t');
                if (tab <= 0) continue;
                String[] parts = line.substring(tab + 1).split(",");
                int[] e = new int[parts.length];
                int n = 0;
                for (String part : parts) {
                    int colon = part.lastIndexOf(':');
                    int idx = find(part.substring(0, colon));
                    if (idx >= 0) e[n++] = idx << 10 | Math.min(1023, Integer.parseInt(part.substring(colon + 1)));
                }
                next.put(line.substring(0, tab), Arrays.copyOf(e, n));
            }
        } catch (java.io.FileNotFoundException ignored) { }

        pairFile = new File(ctx.getFilesDir(), "user_pairs.tsv");
        if (pairFile.exists()) {
            try (BufferedReader r = new BufferedReader(new InputStreamReader(new FileInputStream(pairFile), "UTF-8"))) {
                String line;
                while ((line = r.readLine()) != null) {
                    int tab = line.lastIndexOf('\t');
                    if (tab > 0) pairs.put(line.substring(0, tab), new int[]{Integer.parseInt(line.substring(tab + 1))});
                }
            } catch (Exception ignored) { }
        }
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

    private int score(int i) { return lm(i) + boost(keys[i]) + pairBoost(keys[i]); }

    // --- context: which words follow which (assets/bigrams.tsv)

    private final Map<String, int[]> next = new HashMap<>();   // word -> followers as (index << 10 | cost)
    private int[] ctxNext;                                     // followers of the word before the cursor

    /** The word before the one being typed ("<s>" at a sentence start, null if unknown); ranks likely followers up. */
    void setContext(String prev) {
        ctxPrev = prev == null ? null : key(prev);
        ctxNext = prev == null ? null : next.get(ctxPrev);
    }

    /** Extra points for word pairs this phone's user types often ("hab dich"). */
    private int pairBoost(String key) {
        if (ctxPrev == null) return 0;
        int[] c = pairs.get(ctxPrev + " " + key);
        return c == null ? 0 : Math.min(c[0] * 35, 210);
    }

    /** Frequency mixed with how likely the word is after the previous one, in the same zipf*100 units. */
    private int lm(int i) {
        if (ctxNext == null) return freq[i];
        int cost = -1;
        for (int e : ctxNext) if (e >>> 10 == i) { cost = e & 1023; break; }
        double uni = Math.pow(10, freq[i] / 100.0 - 9), bi = cost < 0 ? 0 : Math.pow(10, -cost / 100.0);
        return (int) Math.round(100 * (Math.log10(0.75 * bi + 0.25 * uni) + 9));
    }

    private int boost(String key) { return Math.min(userCount(key) * 15, 150); }

    // --- learning

    /** A finished word: counts towards learning new words and ranks familiar ones higher. */
    void used(String word, String prev) {
        used(word);
        if (prev == null || word.length() < 2 || pairs.size() >= 20000) return;
        String k = key(prev) + " " + key(word);
        int[] c = pairs.get(k);
        if (c == null) pairs.put(k, c = new int[]{0});
        c[0]++;
        dirty = true;
    }

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
        final StringBuilder sb = new StringBuilder(), sp = new StringBuilder();
        for (Map.Entry<String, int[]> e : pairs.entrySet()) sp.append(e.getKey()).append('\t').append(e.getValue()[0]).append('\n');
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
                File tmp2 = new File(pairFile.getPath() + ".tmp");
                try (Writer w = new OutputStreamWriter(new FileOutputStream(tmp2), "UTF-8")) {
                    w.write(sp.toString());
                } catch (Exception e) { return; }
                tmp2.renameTo(pairFile);
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
        if (ctxNext != null)                    // likely next words, even if rare on their own
            for (int e : ctxNext) {
                int i = e >>> 10;
                if (keys[i].startsWith(w) && !out.containsKey(keys[i])) {
                    int s = score(i) - (keys[i].length() - w.length()) * 8 + (keys[i].equals(w) ? 120 : 0);
                    out.put(keys[i], new Suggestion(keys[i], shown[i] != null ? shown[i] : keys[i], s, false));
                }
            }
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

    // --- swipe typing

    private static final int N = 32;           // points both shapes are resampled to
    // weights of the swipe score, tuned on simulated sloppy swipes (corner cutting, misses by a third of a key)
    static int ALIGN_W = 600, SHAPE_W = 800, NSHAPE_W = 0, LEN_W = 200, ODD_PENALTY = 150;
    static float LM_SCALE = 1.4f;               // how much frequency and context count against the shape
    static float END_R = 1.6f, DEAD = 0.3f, THIN = 0.25f;
    static float PULL = 0.25f, PULL_END = 0.15f, PULL_MAX = 0.7f;  // how far fingers cut corners and stop short, in keys     // how far start/end may miss their key; misses this small cost nothing

    /** Evenly spaced points along a polyline, so a drawn path and a word's ideal path can be compared. */
    private static float[] resample(float[] xs, float[] ys, int m) {
        float[] out = new float[2 * N];
        float total = 0;
        for (int i = 1; i < m; i++) total += (float) Math.hypot(xs[i] - xs[i - 1], ys[i] - ys[i - 1]);
        if (m == 1 || total == 0) {
            for (int i = 0; i < N; i++) { out[2 * i] = xs[0]; out[2 * i + 1] = ys[0]; }
            return out;
        }
        float step = total / (N - 1), walked = 0;
        int seg = 1;
        for (int i = 0; i < N; i++) {
            float target = i * step;
            while (seg < m - 1 && walked + (float) Math.hypot(xs[seg] - xs[seg - 1], ys[seg] - ys[seg - 1]) < target) {
                walked += (float) Math.hypot(xs[seg] - xs[seg - 1], ys[seg] - ys[seg - 1]);
                seg++;
            }
            float len = (float) Math.hypot(xs[seg] - xs[seg - 1], ys[seg] - ys[seg - 1]);
            float t = len == 0 ? 0 : Math.max(0, Math.min(1, (target - walked) / len));
            out[2 * i] = xs[seg - 1] + t * (xs[seg] - xs[seg - 1]);
            out[2 * i + 1] = ys[seg - 1] + t * (ys[seg] - ys[seg - 1]);
        }
        return out;
    }

    /** The points moved to their centre and scaled to size 1, to compare shapes whatever their size. */
    private static float[] normalized(float[] pts) {
        float cx = 0, cy = 0, minX = Float.MAX_VALUE, maxX = -Float.MAX_VALUE, minY = Float.MAX_VALUE, maxY = -Float.MAX_VALUE;
        for (int i = 0; i < N; i++) {
            cx += pts[2 * i]; cy += pts[2 * i + 1];
            minX = Math.min(minX, pts[2 * i]); maxX = Math.max(maxX, pts[2 * i]);
            minY = Math.min(minY, pts[2 * i + 1]); maxY = Math.max(maxY, pts[2 * i + 1]);
        }
        cx /= N; cy /= N;
        float size = Math.max(1f, Math.max(maxX - minX, maxY - minY));
        float[] out = new float[2 * N];
        for (int i = 0; i < N; i++) { out[2 * i] = (pts[2 * i] - cx) / size; out[2 * i + 1] = (pts[2 * i + 1] - cy) / size; }
        return out;
    }

    /** A swipe in key units: x in key widths, y in key heights (keys are taller than wide). */
    private static final class Path {
        float[] x, y, drawn, drawnN;
        int m;
        float len;
        float[] kx = new float[0x100], ky = new float[0x100];   // key centres, same units
        String starts, ends;
        boolean loose;
        char[] chars;
        final float[][] missTab = new float[0x100][];         // per key: miss() to every path point, built when needed

        float[] misses(char c) {
            float[] t = missTab[c];
            if (t == null) {
                t = missTab[c] = new float[m];
                for (int j = 0; j < m; j++) t[j] = miss(kx[c] - x[j], ky[c] - y[j]);
            }
            return t;
        }
    }

    /**
     * Words for a finger path drawn across the letter keys. cx/cy hold each letter's key centre in pixels
     * (indexed by char, NaN where there is no key). A word qualifies when it starts and ends near the
     * path's ends; it is ranked by how well its letters line up with the path in order, how closely the
     * path follows its shape, and how likely it is after the previous word (setContext).
     */
    List<Suggestion> swipe(float[] rawX, float[] rawY, float[] cx, float[] cy, float keyW, float keyH, int max) {
        List<Suggestion> r = swipe(rawX, rawY, cx, cy, keyW, keyH, max, false);
        return r.isEmpty() ? swipe(rawX, rawY, cx, cy, keyW, keyH, max, true) : r;   // nothing fits: try anything nearby
    }

    private List<Suggestion> swipe(float[] rawX, float[] rawY, float[] cx, float[] cy, float keyW, float keyH, int max, boolean loose) {
        Path p = new Path();
        p.x = new float[rawX.length];
        p.y = new float[rawY.length];
        for (int i = 0; i < rawX.length; i++) {          // thin the path: points at least a quarter key apart
            float x = rawX[i] / keyW, y = rawY[i] / keyH;
            if (p.m > 0 && i < rawX.length - 1 && Math.hypot(x - p.x[p.m - 1], y - p.y[p.m - 1]) < THIN) continue;
            p.x[p.m] = x; p.y[p.m] = y; p.m++;
        }
        for (int i = 1; i < p.m; i++) p.len += (float) Math.hypot(p.x[i] - p.x[i - 1], p.y[i] - p.y[i - 1]);
        p.drawn = resample(p.x, p.y, p.m);
        p.drawnN = normalized(p.drawn);
        StringBuilder starts = new StringBuilder(), ends = new StringBuilder();
        float bs = Float.MAX_VALUE, be = Float.MAX_VALUE;
        for (char c = 'a'; c < 0x100; c++) {
            p.kx[c] = cx[c] / keyW;
            p.ky[c] = cy[c] / keyH;
            if (Float.isNaN(cx[c]) || !Character.isLetter(c)) continue;
            bs = Math.min(bs, (float) Math.hypot(p.kx[c] - p.x[0], p.ky[c] - p.y[0]));
            be = Math.min(be, (float) Math.hypot(p.kx[c] - p.x[p.m - 1], p.ky[c] - p.y[p.m - 1]));
        }
        for (char c = 'a'; c < 0x100; c++) {             // keys near the start and the end (and the nearest ones)
            if (Float.isNaN(cx[c]) || !Character.isLetter(c)) continue;
            float r = loose ? 2.5f : END_R;
            if (Math.hypot(p.kx[c] - p.x[0], p.ky[c] - p.y[0]) < Math.max(r, bs + 0.45f)) starts.append(c);
            if (Math.hypot(p.kx[c] - p.x[p.m - 1], p.ky[c] - p.y[p.m - 1]) < Math.max(r, be + 0.45f)) ends.append(c);
        }
        p.starts = starts.toString();
        p.ends = ends.toString();
        p.loose = loose;

        Map<String, Suggestion> out = new HashMap<>();
        float[] wx = new float[48], wy = new float[48], dp = new float[p.m];
        p.chars = new char[48];
        for (int s = 0; s < p.starts.length(); s++) {
            for (int i : prefixRange(String.valueOf(p.starts.charAt(s)))) {
                int sc = swipeShape(keys[i], p, wx, wy, dp);
                if (sc != Integer.MIN_VALUE)
                    out.put(keys[i], new Suggestion(keys[i], shown[i] != null ? shown[i] : keys[i],
                            sc + Math.round(LM_SCALE * score(i)) - (doubtful.get(i) ? ODD_PENALTY : 0), false));
            }
        }
        for (Map.Entry<String, int[]> e : user.entrySet()) {
            String k = e.getKey();
            if (e.getValue()[0] < KNOWN || find(k) >= 0 || p.starts.indexOf(k.charAt(0)) < 0) continue;
            int sc = swipeShape(k, p, wx, wy, dp);
            if (sc != Integer.MIN_VALUE) out.put(k, new Suggestion(k, userShown.get(k), sc + 350 + boost(k), false));
        }
        List<Suggestion> list = new ArrayList<>(out.values());
        java.util.Collections.sort(list, new java.util.Comparator<Suggestion>() {
            public int compare(Suggestion a, Suggestion b) { return b.score - a.score; }
        });
        return list.size() > max ? new ArrayList<>(list.subList(0, max)) : list;
    }

    /** How well the path fits a word (higher is better, around -100 for a good fit), or MIN_VALUE if not at all. */
    private static int swipeShape(String w, Path p, float[] wx, float[] wy, float[] dp) {
        int n = w.length();
        if (n < 2 || n > 40) return Integer.MIN_VALUE;
        char last = w.charAt(n - 1) == 'ß' ? 's' : w.charAt(n - 1);
        if (p.ends.indexOf(last) < 0) return Integer.MIN_VALUE;
        int k = 0;
        char prev = 0;
        char[] wc = p.chars;
        for (int i = 0; i < n; i++) {
            char c = w.charAt(i);
            if (c == 'ß') c = 's';
            if (c >= 0x100 || Float.isNaN(p.kx[c])) return Integer.MIN_VALUE;   // apostrophe, é ...: not swipeable
            if (c == prev) continue;                                            // double letters are one key
            prev = c;
            wc[k] = c; wx[k] = p.kx[c]; wy[k] = p.ky[c]; k++;
        }
        if (k < 2) return Integer.MIN_VALUE;
        float idealLen = 0;
        for (int i = 1; i < k; i++) idealLen += (float) Math.hypot(wx[i] - wx[i - 1], wy[i] - wy[i - 1]);
        float ratio = (p.len + 1) / (idealLen + 1);
        if (ratio > 2.2f || ratio < 0.45f) return Integer.MIN_VALUE;
        // line the letters up with the path in order: each letter takes the closest point after the previous one
        int m = p.m;
        // a corner the finger cuts short or an end it stops before by less than DEAD keys costs nothing
        float limit = (p.loose ? 3f : 1.0f) * k;
        for (int j = 0; j < m; j++) dp[j] = j == 0 ? p.misses(wc[0])[0] : Float.MAX_VALUE;
        for (int i = 1; i < k; i++) {
            float best = Float.MAX_VALUE, rowMin = Float.MAX_VALUE;
            float[] t = p.misses(wc[i]);
            for (int j = 0; j < m; j++) {
                if (dp[j] < best) best = dp[j];
                dp[j] = best == Float.MAX_VALUE ? Float.MAX_VALUE : best + t[j];
                if (dp[j] < rowMin) rowMin = dp[j];
            }
            if (rowMin > limit) return Integer.MIN_VALUE;   // already too far off: stop early
        }
        float align = dp[m - 1] / k;
        if (align * k > limit) return Integer.MIN_VALUE;
        // compare with the path a finger really draws: corners cut, the end reached a little early
        float[] hx = new float[k], hy = new float[k];
        for (int i = 0; i < k; i++) {
            float tx, ty, f;
            if (i == 0) { hx[i] = wx[i]; hy[i] = wy[i]; continue; }
            if (i == k - 1) { tx = wx[i - 1]; ty = wy[i - 1]; f = PULL_END; }
            else { tx = (wx[i - 1] + wx[i + 1]) / 2; ty = (wy[i - 1] + wy[i + 1]) / 2; f = PULL; }
            float dx = tx - wx[i], dy = ty - wy[i], dist = (float) Math.hypot(dx, dy);
            float move = Math.min(f * dist, PULL_MAX);
            hx[i] = dist == 0 ? wx[i] : wx[i] + dx / dist * move;
            hy[i] = dist == 0 ? wy[i] : wy[i] + dy / dist * move;
        }
        float[] ideal = resample(hx, hy, k), idealN = normalized(ideal);
        float d = 0, dn = 0;
        for (int i = 0; i < N; i++) {
            d += (float) Math.hypot(ideal[2 * i] - p.drawn[2 * i], ideal[2 * i + 1] - p.drawn[2 * i + 1]);
            dn += (float) Math.hypot(idealN[2 * i] - p.drawnN[2 * i], idealN[2 * i + 1] - p.drawnN[2 * i + 1]);
        }
        return Math.round(-ALIGN_W * align - SHAPE_W * d / N - NSHAPE_W * dn / N - LEN_W * Math.abs((float) Math.log(ratio)));
    }

    private static float miss(float dx, float dy) {
        return Math.max(0f, (float) Math.hypot(dx, dy) - DEAD);
    }
}
