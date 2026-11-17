package de.spaceage.tvapp;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;

/** Zeiger für Seiten, die nicht für die Fernbedienung gebaut sind (wie in Silk): Ring mit Punkt. */
final class CursorView extends View {
    float x, y;
    final float r;
    final Paint ring = new Paint(Paint.ANTI_ALIAS_FLAG), fill = new Paint(Paint.ANTI_ALIAS_FLAG),
            shadow = new Paint(Paint.ANTI_ALIAS_FLAG);

    CursorView(Context c) {
        super(c);
        float d = c.getResources().getDisplayMetrics().density;
        r = 14 * d;
        ring.setStyle(Paint.Style.STROKE); ring.setStrokeWidth(3 * d); ring.setColor(Color.WHITE);
        shadow.setStyle(Paint.Style.STROKE); shadow.setStrokeWidth(6 * d); shadow.setColor(0x99000000);
        fill.setColor(0x664FD1C5);
        setFocusable(false);
        setClickable(false);
    }

    @Override
    protected void onDraw(Canvas c) {
        c.drawCircle(x, y, r, shadow);
        c.drawCircle(x, y, r, fill);
        c.drawCircle(x, y, r, ring);
        c.drawCircle(x, y, r * .18f, ring);
    }
}
