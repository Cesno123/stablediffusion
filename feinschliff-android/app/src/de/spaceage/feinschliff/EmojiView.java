package de.spaceage.feinschliff;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;

/** The emoji panel: category tabs, a scrolling grid, recently used first, and ABC / space / delete. */
final class EmojiView extends LinearLayout {
    interface Listener {
        void onEmoji(String emoji);
        void onEmojiDelete();
        void onEmojiSpace();
        void onEmojiClose();
    }

    private static final String[] TABS = {"🕘", "😀", "👋", "❤️", "🐶", "🍕", "⚽", "🚗", "💡", "✅", "🏳️"};
    private static final String[] EMOJIS = {
            "",   // recently used, filled from the preferences
            "😀 😃 😄 😁 😆 😅 🤣 😂 🙂 🙃 🫠 😉 😊 😇 🥰 😍 🤩 😘 😗 ☺️ 😚 😙 🥲 😋 😛 😜 🤪 😝 🤑 🤗 🤭 🫢 🫣 🤫 🤔 🫡 "
                    + "🤐 🤨 😐 😑 😶 🫥 😏 😒 🙄 😬 😮‍💨 🤥 😌 😔 😪 🤤 😴 😷 🤒 🤕 🤢 🤮 🤧 🥵 🥶 🥴 😵 😵‍💫 🤯 🤠 🥳 🥸 😎 🤓 🧐 "
                    + "😕 🫤 😟 🙁 ☹️ 😮 😯 😲 😳 🥺 🥹 😦 😧 😨 😰 😥 😢 😭 😱 😖 😣 😞 😓 😩 😫 🥱 😤 😡 😠 🤬 😈 👿 💀 ☠️ 💩 "
                    + "🤡 👹 👺 👻 👽 👾 🤖 😺 😸 😹 😻 😼 😽 🙀 😿 😾 🙈 🙉 🙊",
            "👋 🤚 🖐️ ✋ 🖖 🫱 🫲 👌 🤌 🤏 ✌️ 🤞 🫰 🤟 🤘 🤙 👈 👉 👆 🖕 👇 ☝️ 🫵 👍 👎 ✊ 👊 🤛 🤜 👏 🙌 🫶 👐 🤲 🤝 🙏 "
                    + "✍️ 💅 🤳 💪 🦾 🦵 🦶 👂 👃 🧠 👀 👁️ 👅 👄 🫦 👶 🧒 👦 👧 🧑 👱 👨 🧔 👩 🧓 👴 👵 🙍 🙎 🙅 🙆 💁 🙋 🧏 🙇 "
                    + "🤦 🤷 👮 🕵️ 💂 👷 🤴 👸 👳 🤵 👰 🤰 🤱 👼 🎅 🤶 🦸 🦹 🧙 🧚 🧛 🧜 🧝 🧞 🧟 💆 💇 🚶 🧍 🧎 🏃 💃 🕺 👯 🧖 "
                    + "🧗 🏇 🏂 🏌️ 🏄 🚣 🏊 ⛹️ 🏋️ 🚴 🚵 🤸 🤼 🤽 🤾 🤹 🧘 🛀 🛌 👭 👫 👬 💏 💑 👪 🗣️ 👤 👥 👣",
            "❤️ 🧡 💛 💚 💙 🩵 💜 🤎 🖤 🩶 🤍 🩷 💔 ❤️‍🔥 ❤️‍🩹 ❣️ 💕 💞 💓 💗 💖 💘 💝 💟 💌 💋 💯 💢 💥 💫 💦 💨 🕳️ 💬 "
                    + "🗨️ 🗯️ 💭 💤 🌹 🥀 🌷 🌸 💐 🌺 🌻 🌼 💍 💎 🎁 🎀 🎉 🎊 🥂 🍾 🔥 ✨ ⭐ 🌟 🌈 ☀️ 🌙",
            "🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐻‍❄️ 🐨 🐯 🦁 🐮 🐷 🐽 🐸 🐵 🐔 🐧 🐦 🐤 🐣 🐥 🦆 🦅 🦉 🦇 🐺 🐗 🐴 🦄 🐝 🪱 🐛 🦋 🐌 "
                    + "🐞 🐜 🪰 🪲 🦟 🦗 🕷️ 🦂 🐢 🐍 🦎 🦖 🦕 🐙 🦑 🦐 🦞 🦀 🐡 🐠 🐟 🐬 🐳 🐋 🦈 🦭 🐊 🐅 🐆 🦓 🦍 🦧 🐘 🦛 🦏 "
                    + "🐪 🐫 🦒 🦘 🐃 🐂 🐄 🐎 🐖 🐏 🐑 🦙 🐐 🦌 🐕 🐩 🐈 🐈‍⬛ 🐓 🦃 🦚 🦜 🦢 🦩 🕊️ 🐇 🦝 🦨 🦡 🦫 🦦 🦥 🐁 🐀 🐿️ "
                    + "🦔 🌵 🎄 🌲 🌳 🌴 🪵 🌱 🌿 ☘️ 🍀 🎍 🪴 🎋 🍃 🍂 🍁 🍄 🐚 🪨 🌾 🌍 🌕 🌑 ⭐ ☁️ ⛅ 🌧️ ⛈️ 🌩️ ❄️ ☃️ ⛄ 🌊",
            "🍏 🍎 🍐 🍊 🍋 🍌 🍉 🍇 🍓 🫐 🍈 🍒 🍑 🥭 🍍 🥥 🥝 🍅 🍆 🥑 🥦 🥬 🥒 🌶️ 🫑 🌽 🥕 🫒 🧄 🧅 🥔 🍠 🥐 🥯 🍞 🥖 "
                    + "🥨 🧀 🥚 🍳 🧈 🥞 🧇 🥓 🥩 🍗 🍖 🌭 🍔 🍟 🍕 🫓 🥪 🥙 🧆 🌮 🌯 🫔 🥗 🥘 🫕 🥫 🍝 🍜 🍲 🍛 🍣 🍱 🥟 🦪 🍤 "
                    + "🍙 🍚 🍘 🍥 🥠 🥮 🍢 🍡 🍧 🍨 🍦 🥧 🧁 🍰 🎂 🍮 🍭 🍬 🍫 🍿 🍩 🍪 🌰 🥜 🍯 🥛 🍼 ☕ 🫖 🍵 🧃 🥤 🧋 🍶 🍺 🍻 "
                    + "🥂 🍷 🥃 🍸 🍹 🧉 🍾 🧊 🥄 🍴 🍽️ 🥣 🥡 🥢 🧂",
            "⚽ 🏀 🏈 ⚾ 🥎 🎾 🏐 🏉 🥏 🎱 🪀 🏓 🏸 🏒 🏑 🥍 🏏 🪃 🥅 ⛳ 🪁 🏹 🎣 🤿 🥊 🥋 🎽 🛹 🛼 🛷 ⛸️ 🥌 🎿 ⛷️ 🏂 🪂 "
                    + "🏋️ 🤼 🤸 ⛹️ 🤺 🤾 🏌️ 🏇 🧘 🏄 🏊 🤽 🚣 🧗 🚵 🚴 🏆 🥇 🥈 🥉 🏅 🎖️ 🏵️ 🎗️ 🎫 🎟️ 🎪 🤹 🎭 🩰 🎨 🎬 🎤 🎧 "
                    + "🎼 🎹 🥁 🪘 🎷 🎺 🪗 🎸 🪕 🎻 🎲 ♟️ 🎯 🎳 🎮 🎰 🧩",
            "🚗 🚕 🚙 🚌 🚎 🏎️ 🚓 🚑 🚒 🚐 🛻 🚚 🚛 🚜 🦯 🦽 🦼 🛴 🚲 🛵 🏍️ 🛺 🚨 🚔 🚍 🚘 🚖 🚡 🚠 🚟 🚃 🚋 🚞 🚝 🚄 🚅 "
                    + "🚈 🚂 🚆 🚇 🚊 🚉 ✈️ 🛫 🛬 🛩️ 💺 🛰️ 🚀 🛸 🚁 🛶 ⛵ 🚤 🛥️ 🛳️ ⛴️ 🚢 ⚓ 🪝 ⛽ 🚧 🚦 🚥 🚏 🗺️ 🗿 🗽 🗼 🏰 🏯 "
                    + "🏟️ 🎡 🎢 🎠 ⛲ ⛱️ 🏖️ 🏝️ 🏜️ 🌋 ⛰️ 🏔️ 🗻 🏕️ ⛺ 🛖 🏠 🏡 🏘️ 🏚️ 🏗️ 🏭 🏢 🏬 🏣 🏤 🏥 🏦 🏨 🏪 🏫 🏩 💒 🏛️ ⛪ "
                    + "🕌 🕍 🛕 🕋 ⛩️ 🛤️ 🛣️ 🗾 🎑 🏞️ 🌅 🌄 🌠 🎇 🎆 🌇 🌆 🏙️ 🌃 🌌 🌉 🌁",
            "⌚ 📱 📲 💻 ⌨️ 🖥️ 🖨️ 🖱️ 🖲️ 🕹️ 🗜️ 💽 💾 💿 📀 📼 📷 📸 📹 🎥 📽️ 🎞️ 📞 ☎️ 📟 📠 📺 📻 🎙️ 🎚️ 🎛️ 🧭 ⏱️ ⏲️ ⏰ 🕰️ "
                    + "⌛ ⏳ 📡 🔋 🪫 🔌 💡 🔦 🕯️ 🪔 🧯 🛢️ 💸 💵 💴 💶 💷 🪙 💰 💳 💎 ⚖️ 🪜 🧰 🪛 🔧 🔨 ⚒️ 🛠️ ⛏️ 🪚 🔩 ⚙️ 🪤 🧱 "
                    + "⛓️ 🧲 🔫 💣 🧨 🪓 🔪 🗡️ ⚔️ 🛡️ 🚬 ⚰️ 🪦 ⚱️ 🏺 🔮 📿 🧿 🪬 💈 ⚗️ 🔭 🔬 🕳️ 🩹 🩺 🩻 🩼 💊 💉 🩸 🧬 🦠 🧫 🧪 🌡️ "
                    + "🧹 🪠 🧺 🧻 🚽 🚰 🚿 🛁 🛀 🧼 🪥 🪒 🧽 🪣 🧴 🛎️ 🔑 🗝️ 🚪 🪑 🛋️ 🛏️ 🛌 🧸 🪆 🖼️ 🪞 🪟 🛍️ 🛒 🎁 🎈 🎏 🎀 🪄 "
                    + "🪅 🎊 🎉 🎎 🏮 🎐 🧧 ✉️ 📩 📨 📧 💌 📥 📤 📦 🏷️ 🪧 📪 📫 📬 📭 📮 📯 📜 📃 📄 📑 🧾 📊 📈 📉 🗒️ 🗓️ 📆 📅 "
                    + "🗑️ 📇 🗃️ 🗳️ 🗄️ 📋 📁 📂 🗂️ 🗞️ 📰 📓 📔 📒 📕 📗 📘 📙 📚 📖 🔖 🧷 🔗 📎 🖇️ 📐 📏 🧮 📌 📍 ✂️ 🖊️ 🖋️ ✒️ 🖌️ "
                    + "🖍️ 📝 ✏️ 🔍 🔎 🔏 🔐 🔒 🔓",
            "✅ ☑️ ✔️ ❌ ❎ ➕ ➖ ➗ ✖️ 🟰 ♾️ ‼️ ⁉️ ❓ ❔ ❕ ❗ 〰️ 💱 💲 ⚕️ ♻️ ⚜️ 🔱 📛 🔰 ⭕ ❇️ ✳️ ©️ ®️ ™️ #️⃣ *️⃣ 0️⃣ 1️⃣ "
                    + "2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟 🔠 🔡 🔢 🔣 🔤 🅰️ 🆎 🅱️ 🆑 🆒 🆓 ℹ️ 🆔 Ⓜ️ 🆕 🆖 🅾️ 🆗 🅿️ 🆘 🆙 🆚 🔴 🟠 🟡 "
                    + "🟢 🔵 🟣 🟤 ⚫ ⚪ 🟥 🟧 🟨 🟩 🟦 🟪 🟫 ⬛ ⬜ 🔶 🔷 🔸 🔹 🔺 🔻 💠 🔘 🔳 🔲 ⬆️ ↗️ ➡️ ↘️ ⬇️ ↙️ ⬅️ ↖️ ↕️ ↔️ ↩️ "
                    + "↪️ ⤴️ ⤵️ 🔃 🔄 🔙 🔚 🔛 🔜 🔝 🛐 ⚛️ 🕉️ ✡️ ☸️ ☯️ ✝️ ☦️ ☪️ ☮️ 🕎 🔯 ♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓ ⛎ 🔀 🔁 "
                    + "🔂 ▶️ ⏩ ⏭️ ⏯️ ◀️ ⏪ ⏮️ 🔼 ⏫ 🔽 ⏬ ⏸️ ⏹️ ⏺️ ⏏️ 🎦 🔅 🔆 📶 📳 📴 ♀️ ♂️ ⚧️ 🚻 🚹 🚺 🚼 🚾 ♿ 🚭 🚫 ⛔ 🚷 🔞 "
                    + "☢️ ☣️ ⚠️ 🚸 💤 🎵 🎶 💲 🏧 🔇 🔈 🔉 🔊 🔔 🔕 📣 📢",
            "🏳️ 🏴 🏁 🚩 🏳️‍🌈 🏳️‍⚧️ 🏴‍☠️ 🇩🇪 🇦🇹 🇨🇭 🇪🇺 🇬🇧 🇺🇸 🇫🇷 🇮🇹 🇪🇸 🇵🇹 🇳🇱 🇧🇪 🇱🇺 🇩🇰 🇸🇪 🇳🇴 🇫🇮 🇮🇸 🇮🇪 "
                    + "🇵🇱 🇨🇿 🇸🇰 🇭🇺 🇸🇮 🇭🇷 🇧🇦 🇷🇸 🇲🇪 🇦🇱 🇲🇰 🇬🇷 🇧🇬 🇷🇴 🇲🇩 🇺🇦 🇧🇾 🇷🇺 🇱🇹 🇱🇻 🇪🇪 🇹🇷 🇨🇾 🇲🇹 🇮🇱 🇵🇸 "
                    + "🇱🇧 🇸🇾 🇮🇶 🇮🇷 🇸🇦 🇦🇪 🇶🇦 🇪🇬 🇲🇦 🇹🇳 🇩🇿 🇳🇬 🇬🇭 🇰🇪 🇪🇹 🇿🇦 🇨🇦 🇲🇽 🇨🇺 🇯🇲 🇧🇷 🇦🇷 🇨🇱 🇨🇴 🇵🇪 🇻🇪 "
                    + "🇮🇳 🇵🇰 🇧🇩 🇨🇳 🇯🇵 🇰🇷 🇰🇵 🇹🇭 🇻🇳 🇮🇩 🇵🇭 🇲🇾 🇸🇬 🇦🇺 🇳🇿 🇦🇫 🇰🇿 🇬🇪 🇦🇲 🇦🇿",
    };
    private static final int COLUMNS = 8, MAX_RECENT = 32;

    private final Listener listener;
    private final SharedPreferences prefs;
    private final LinearLayout grid, tabs;
    private final ScrollView scroll;
    private int fg, tabBg, keyBg;
    private int current = -1;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private Runnable repeat;

    EmojiView(Context c, Listener listener, SharedPreferences prefs, boolean dark, int height) {
        super(c);
        this.listener = listener;
        this.prefs = prefs;
        setOrientation(VERTICAL);
        fg = dark ? 0xFFE9EBF1 : 0xFF15171C;
        tabBg = dark ? 0xFF3D4352 : 0xFFB9BECC;
        keyBg = dark ? 0xFF20232B : 0xFFCDD1DA;
        setBackgroundColor(dark ? 0xFF15171C : 0xFFE6E8EE);
        float d = c.getResources().getDisplayMetrics().density;

        tabs = new LinearLayout(c);
        for (int i = 0; i < TABS.length; i++) {
            final int tab = i;
            TextView t = cell(TABS[i], 20);
            t.setOnClickListener(new OnClickListener() { public void onClick(View v) { show(tab); } });
            tabs.addView(t, new LayoutParams(Math.round(44 * d), Math.round(40 * d)));
        }
        HorizontalScrollView tabScroll = new HorizontalScrollView(c);
        tabScroll.setHorizontalScrollBarEnabled(false);
        tabScroll.addView(tabs);
        addView(tabScroll);

        scroll = new ScrollView(c);
        grid = new LinearLayout(c);
        grid.setOrientation(VERTICAL);
        scroll.addView(grid);
        int bottomH = Math.round(48 * d), tabsH = Math.round(40 * d);
        addView(scroll, new LayoutParams(LayoutParams.MATCH_PARENT, Math.max(Math.round(120 * d), height - bottomH - tabsH)));

        LinearLayout bottom = new LinearLayout(c);
        TextView abc = key("ABC");
        abc.setOnClickListener(new OnClickListener() { public void onClick(View v) { EmojiView.this.listener.onEmojiClose(); } });
        TextView space = key("Leertaste");
        space.setOnClickListener(new OnClickListener() { public void onClick(View v) { EmojiView.this.listener.onEmojiSpace(); } });
        TextView del = key("⌫");
        del.setOnTouchListener(new OnTouchListener() {          // hold to keep deleting, like the keyboard
            public boolean onTouch(View v, MotionEvent e) {
                if (e.getActionMasked() == MotionEvent.ACTION_DOWN) {
                    EmojiView.this.listener.onEmojiDelete();
                    repeat = new Runnable() { public void run() { EmojiView.this.listener.onEmojiDelete(); handler.postDelayed(this, 60); } };
                    handler.postDelayed(repeat, 400);
                } else if (e.getActionMasked() == MotionEvent.ACTION_UP || e.getActionMasked() == MotionEvent.ACTION_CANCEL) {
                    if (repeat != null) handler.removeCallbacks(repeat);
                    repeat = null;
                }
                return true;
            }
        });
        bottom.addView(abc, new LayoutParams(0, bottomH, 1.5f));
        bottom.addView(space, new LayoutParams(0, bottomH, 5f));
        bottom.addView(del, new LayoutParams(0, bottomH, 1.5f));
        addView(bottom);
        show(recent().isEmpty() ? 1 : 0);
    }

    private TextView cell(String s, int size) {
        TextView t = new TextView(getContext());
        t.setText(s);
        t.setTextSize(size);
        t.setGravity(Gravity.CENTER);
        t.setTextColor(fg);
        return t;
    }

    private TextView key(String s) {
        TextView t = cell(s, 15);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setBackgroundColor(keyBg);
        return t;
    }

    private List<String> recent() {
        List<String> out = new ArrayList<String>();
        for (String e : prefs.getString("recentEmoji", "").split(" ")) if (!e.isEmpty()) out.add(e);
        return out;
    }

    private void remember(String e) {
        List<String> r = recent();
        r.remove(e);
        r.add(0, e);
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < r.size() && i < MAX_RECENT; i++) sb.append(r.get(i)).append(' ');
        prefs.edit().putString("recentEmoji", sb.toString().trim()).apply();
    }

    private void show(int tab) {
        current = tab;
        for (int i = 0; i < tabs.getChildCount(); i++) tabs.getChildAt(i).setBackgroundColor(i == tab ? tabBg : 0);
        grid.removeAllViews();
        List<String> list = new ArrayList<String>();
        if (tab == 0) list.addAll(recent());
        else for (String e : EMOJIS[tab].split(" ")) if (!e.isEmpty()) list.add(e);
        if (list.isEmpty()) {
            TextView hint = cell("Hier erscheinen deine zuletzt benutzten Emojis.", 14);
            grid.addView(hint, new LayoutParams(LayoutParams.MATCH_PARENT, Math.round(80 * getResources().getDisplayMetrics().density)));
        }
        float d = getResources().getDisplayMetrics().density;
        LinearLayout row = null;
        for (int i = 0; i < list.size(); i++) {
            if (i % COLUMNS == 0) {
                row = new LinearLayout(getContext());
                grid.addView(row, new LayoutParams(LayoutParams.MATCH_PARENT, Math.round(46 * d)));
            }
            final String e = list.get(i);
            TextView t = cell(e, 26);
            t.setOnClickListener(new OnClickListener() {
                public void onClick(View v) { remember(e); listener.onEmoji(e); }
            });
            row.addView(t, new LayoutParams(0, LayoutParams.MATCH_PARENT, 1f));
        }
        if (row != null) for (int i = list.size() % COLUMNS; i > 0 && i < COLUMNS; i++)   // keep the last row's cells the same width
            row.addView(new View(getContext()), new LayoutParams(0, LayoutParams.MATCH_PARENT, 1f));
        scroll.scrollTo(0, 0);
    }

    @Override
    protected void onVisibilityChanged(View changed, int visibility) {
        super.onVisibilityChanged(changed, visibility);
        if (visibility != VISIBLE && repeat != null) { handler.removeCallbacks(repeat); repeat = null; }
    }

    /** Opening the panel shows the recently used emojis, if there are any. */
    void reset() { show(recent().isEmpty() ? 1 : 0); }
}
