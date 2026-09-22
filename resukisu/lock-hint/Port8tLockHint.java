package com.oplus.uifirst;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

/** Caller-local fallback for the separately versioned Kebab lock-hint ABI. */
public final class Port8tLockHint {
    private static final String NODE = "/proc/oplus_scheduler/sched_assist/lock_hint";
    private static final boolean SUPPORTED = supported();
    private static final ThreadLocal<State> LOCAL = new ThreadLocal<State>() {
        @Override protected State initialValue() { return new State(new Driver()); }
    };
    private Port8tLockHint() {}
    private static boolean supported() {
        try (FileInputStream in = new FileInputStream(NODE)) {
            byte[] bytes = new byte[64];
            int count = in.read(bytes);
            return count > 0 && new String(bytes, 0, count, StandardCharsets.US_ASCII)
                    .startsWith("port8t_lock_hint_v1 ");
        } catch (IOException | SecurityException unavailable) { return false; }
    }
    public static void hint(boolean enter, int nativeResult) {
        if (SUPPORTED) LOCAL.get().change(enter, nativeResult);
    }
    interface Writer {
        void write(boolean enter) throws IOException;
        void discard();
    }
    static final class Driver implements Writer {
        private FileOutputStream out;
        public void write(boolean enter) throws IOException {
            if (out == null) out = new FileOutputStream(NODE);
            out.write(enter ? 49 : 48);
        }
        public void discard() {
            if (out != null) {
                try { out.close(); } catch (IOException ignored) { }
                out = null;
            }
        }
    }
    static final class State {
        final Writer writer;
        int depth;
        boolean owned;
        State(Writer writer) { this.writer = writer; }
        void change(boolean enter, int nativeResult) {
            if (enter) {
                if (depth == Integer.MAX_VALUE) throw new IllegalStateException("lock hint depth overflow");
                if (depth++ != 0 || nativeResult == 0) return;
                try {
                    writer.write(true);
                    owned = true;
                } catch (IOException | SecurityException unavailable) {
                    writer.discard();
                }
            } else {
                if (depth == 0 || --depth != 0 || !owned) return;
                try { writer.write(false); }
                catch (IOException | SecurityException unavailable) { writer.discard(); }
                finally { owned = false; }
            }
        }
    }
}
