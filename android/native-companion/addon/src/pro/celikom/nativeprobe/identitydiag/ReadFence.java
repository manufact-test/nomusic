package pro.celikom.nativeprobe.identitydiag;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.util.concurrent.*;
import java.util.function.BooleanSupplier;
/** Cancels obsolete read-only HTTP operations; never used for token rotation or writes. */
final class ReadFence implements AutoCloseable {
 final BooleanSupplier valid;final ScheduledExecutorService timer;
 ReadFence(HttpURLConnection connection,BooleanSupplier valid){this.valid=valid;timer=valid==null?null:Executors.newSingleThreadScheduledExecutor();if(timer!=null)timer.scheduleAtFixedRate(()->{if(!valid.getAsBoolean())connection.disconnect();},100,100,TimeUnit.MILLISECONDS);}
 void check()throws IOException{if(valid!=null&&!valid.getAsBoolean())throw new IOException("lookup_cancelled");}
 public void close(){if(timer!=null)timer.shutdownNow();}
}
