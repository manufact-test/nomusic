package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaDataSource;
import java.io.IOException;
/** Android codec adapter; transport/cache logic is exercised by host tests. */
final class StreamingAudio extends MediaDataSource {
 final BufferedAudio audio;StreamingAudio(BufferedAudio audio){this.audio=audio;}
 public long getSize(){return audio.size;}
 public int readAt(long position,byte[] buffer,int offset,int size)throws IOException{return audio.readAt(position,buffer,offset,size);}
 public void close(){audio.close();}
}
