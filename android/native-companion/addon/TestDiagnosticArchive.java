package pro.celikom.nativeprobe.identitydiag;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
public class TestDiagnosticArchive {
 static int checks;static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static String snapshot(DiagnosticArchive archive,DiagnosticJournal journal)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();archive.copyTo(out);journal.copyTo(out);return out.toString("UTF-8");}
 public static void main(String[] args)throws Exception{
  Path directory=Files.createTempDirectory("celikom-run-history-");DiagnosticJournal journal=new DiagnosticJournal(directory.resolve("report.txt").toFile(),64);DiagnosticArchive archive=new DiagnosticArchive(journal.current);journal.reset();
  archive.remember(journal);check(!archive.available(),"empty startup cannot invent previous runs");
  journal.append("run-one fault\n".getBytes(StandardCharsets.UTF_8));archive.remember(journal);journal.reset();journal.append("run-two restart\n".getBytes(StandardCharsets.UTF_8));String value=snapshot(archive,journal);check(value.equals("run-one fault\nrun-two restart\n"),"Stop/Start retains the prior fault in chronological export order");
  archive.remember(journal);journal.reset();journal.append("run-three\n".getBytes(StandardCharsets.UTF_8));check(snapshot(archive,journal).startsWith("run-one fault\nrun-two restart\nrun-three"),"two earlier runs remain available");
  archive.remember(journal);journal.reset();journal.append("run-four\n".getBytes(StandardCharsets.UTF_8));value=snapshot(archive,journal);check(!value.contains("run-one")&&value.equals("run-two restart\nrun-three\nrun-four\n"),"history has a fixed two-run retention bound");
  for(int run=0;run<100;run++){archive.remember(journal);journal.reset();for(int row=0;row<100;row++)journal.append(("run="+run+" row="+row+"\n").getBytes(StandardCharsets.UTF_8));check(archive.recent.length()<=128&&archive.older.length()<=128,"each archived run has only the two bounded diagnostic segments");}
  check(!archive.temp.exists(),"rotation leaves no staging file behind");check(snapshot(archive,journal).contains("run=99 row=99"),"export reaches the current run's last event");for(File file:directory.toFile().listFiles())Files.delete(file.toPath());Files.delete(directory);
  System.out.println("PASS: "+checks+" bounded previous-run preservation checks");
 }
}
