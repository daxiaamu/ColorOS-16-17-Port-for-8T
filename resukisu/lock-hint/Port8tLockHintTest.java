package com.oplus.uifirst;
import java.io.IOException;
public final class Port8tLockHintTest {
 static class W implements Port8tLockHint.Writer {
  int starts,ends,closes; boolean failStart,failEnd;
  public void write(boolean on) throws IOException {
   if(on){starts++;if(failStart)throw new IOException();}
   else {ends++;if(failEnd)throw new IOException();}
  }
  public void discard(){closes++;}
 }
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
  W w=new W();Port8tLockHint.State s=new Port8tLockHint.State(w);
  s.change(true,-1);s.change(true,-1);check(w.starts==1 && s.depth==2);
  s.change(false,-1);check(w.ends==0);s.change(false,-1);check(w.ends==1 && !s.owned && s.depth==0);
  s.change(false,-1);check(w.ends==1);
  s.change(true,0);s.change(true,-1);s.change(false,-1);s.change(false,0);check(w.starts==1 && w.ends==1);
  w.failStart=true;s.change(true,-1);s.change(false,-1);check(w.ends==1 && !s.owned && s.depth==0);
  w.failStart=false;w.failEnd=true;s.change(true,-1);s.change(false,-1);check(!s.owned && s.depth==0 && w.closes==2);
  w.failEnd=false;s.change(true,-1);s.change(false,-1);check(w.starts==4 && w.ends==3);
  System.out.println("PASS nested pairing, native success, unmatched exit, enter/exit failure, retry");
 }
}
