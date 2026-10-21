package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
/** Preserve two preceding runs so a roadside Stop/Start cannot erase the fault. */
final class DiagnosticArchive {
 final File recent,older,temp;
 DiagnosticArchive(File source){recent=new File(source.getPath()+".run-1");older=new File(source.getPath()+".run-2");temp=new File(source.getPath()+".run-tmp");}
 void remember(DiagnosticJournal journal)throws IOException{
  if(journal.current.length()==0&&journal.previous.length()==0)return;
  try{
   try(OutputStream out=new FileOutputStream(temp)){journal.copyTo(out);}
   if(older.exists()&&!older.delete())throw new IOException("archive_rotation_failed");
   if(recent.exists()&&!recent.renameTo(older))throw new IOException("archive_rotation_failed");
   if(!temp.renameTo(recent))throw new IOException("archive_rotation_failed");
  }finally{temp.delete();}
 }
 void copyTo(OutputStream out)throws IOException{DiagnosticJournal.copy(older,out);DiagnosticJournal.copy(recent,out);}
 boolean available(){return recent.length()>0||older.length()>0;}
}
