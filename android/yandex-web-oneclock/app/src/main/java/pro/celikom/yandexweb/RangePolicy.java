package pro.celikom.yandexweb;

/** RFC 7233 single-byte-range implementation, independent of Android SDK. */
public final class RangePolicy {
  private RangePolicy(){}
  public static final class Selection {
    public final long start,end,total;
    public final boolean partial;
    Selection(long start,long end,long total,boolean partial) {
      this.start=start;this.end=end;this.total=total;this.partial=partial;
    }
    public long length(){return end-start+1;}
    public int status(){return partial?206:200;}
    public String contentRange(){return "bytes "+start+"-"+end+"/"+total;}
  }
  public static Selection parse(String input,long total){
    if(total<=0)throw new IllegalArgumentException("empty file");
    if(input==null||input.trim().isEmpty())return new Selection(0,total-1,total,false);
    if(!input.startsWith("bytes=")||input.indexOf(',')>=0)throw new IllegalArgumentException("bad range");
    String spec=input.substring(6);
    if(!spec.matches("[0-9]*-[0-9]*")||"-".equals(spec))throw new IllegalArgumentException("bad range");
    String[] tokens=spec.split("-",2);
    long start,end;
    try{
      if(tokens[0].isEmpty()){
        long suffix=Long.parseLong(tokens[1]);
        if(suffix<=0)throw new IllegalArgumentException("bad suffix");
        start=Math.max(0,total-suffix);
        end=total-1;
      }else{
        start=Long.parseLong(tokens[0]);
        end=tokens[1].isEmpty()?total-1:Math.min(total-1,Long.parseLong(tokens[1]));
      }
    }catch(NumberFormatException error){throw new IllegalArgumentException("bad range");}
    if(start<0||start>=total||end<start)throw new IllegalArgumentException("unsatisfiable range");
    return new Selection(start,end,total,true);
  }
}
