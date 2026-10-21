package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
/** Two bounded local segments. Rotation never controls playback lifetime. */
final class DiagnosticJournal {
 final File current,previous;final long limit;
 DiagnosticJournal(File current,long limit){this.current=current;this.previous=new File(current.getPath()+".previous");this.limit=limit;}
 void reset()throws IOException{if(previous.exists()&&!previous.delete())throw new IOException("journal_reset_failed");try(FileOutputStream out=new FileOutputStream(current)){} }
 void append(byte[] bytes)throws IOException{
  if(bytes.length>limit)throw new IOException("journal_record_too_large");
  if(current.length()+bytes.length>limit){
   if(previous.exists()&&!previous.delete())throw new IOException("journal_rotation_failed");
   if(current.exists()&&!current.renameTo(previous))throw new IOException("journal_rotation_failed");
  }
  try(FileOutputStream out=new FileOutputStream(current,true)){out.write(bytes);}
 }
 void copyTo(OutputStream out)throws IOException{copy(previous,out);copy(current,out);}
 static void copy(File file,OutputStream out)throws IOException{if(!file.exists())return;try(InputStream in=new FileInputStream(file)){byte[] b=new byte[16384];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}}
}
