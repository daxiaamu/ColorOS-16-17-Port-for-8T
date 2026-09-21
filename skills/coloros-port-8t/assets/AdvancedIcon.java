package com.oplus.settings.port8t;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;

/** Transparent OS17-style adjustment glyph; uses the native 24dp preference slot. */
public final class AdvancedIcon extends Drawable {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final int size;
    private int opacity = 255;

    public AdvancedIcon(Context context) {
        size = Math.round(24f * context.getResources().getDisplayMetrics().density);
    }

    private void color(int rgb) {
        paint.setColor(rgb);
        paint.setAlpha(opacity);
    }

    private void slider(Canvas canvas, float y, float x) {
        color(0xff79bfff);
        canvas.drawRoundRect(1f, y - 1.2f, 23f, y + 1.2f, 1.2f, 1.2f, paint);
        color(0xff0088ff);
        canvas.drawRoundRect(x - 2.8f, y - 3.5f, x + 2.8f, y + 3.5f, 2f, 2f, paint);
    }

    @Override public void draw(Canvas canvas) {
        Rect bounds = getBounds();
        if (bounds.isEmpty()) return;
        int save = canvas.save();
        canvas.translate(bounds.left, bounds.top);
        canvas.scale(bounds.width() / 24f, bounds.height() / 24f);
        slider(canvas, 4f, 7f);
        slider(canvas, 12f, 17f);
        slider(canvas, 20f, 9f);
        canvas.restoreToCount(save);
    }

    @Override public int getIntrinsicWidth() { return size; }
    @Override public int getIntrinsicHeight() { return size; }
    @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    @Override public void setAlpha(int alpha) {
        opacity = Math.max(0, Math.min(255, alpha));
        invalidateSelf();
    }
    @Override public void setColorFilter(ColorFilter filter) {
        paint.setColorFilter(filter);
        invalidateSelf();
    }
}
