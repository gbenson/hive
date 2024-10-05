import json

from base64 import a85decode

import pytest

from hive.reading_list_updater.entry import ReadingListEntry

# https://github.com/gbenson/hivebot/blob/main/tests/readinglist_tests.py


@pytest.mark.parametrize(
    ("description", "email_bytes", "expect_wikitext"),
    (("URL-only generic link",
      a85decode(r"""
6t(1K3Zq.8DCcnc3$:t7Fs&Oo1,9t,2EEQQ3\rc=/MJk40F\@YEc5eU+@fj\Gp#FbDKB`6+?
X:FEd9o_@V'FuDf.1FATU*F$:A`LFCf?3/Q@"7ANCrUAU&;ME,8rsDEAtNBOPq&ATU'ZF`_4
I3$Je=6Z6jaASuTA<,uDbF(T!(/OaPeDe*R"B0%.o@VKon$;F)d74hPOEcYr5DE8mp/hd_A%
16cjFDu:^0/%9YDJsQ0@4l&.D(fR@G:doT/UD,M/Tc2T/R`[?@<loGBl5M;@<Q(#@rc:&F>"
(1"""),
      "{{at|Mon, 28 Nov 2022 16:19:39 -0000}} "
      "https://pinoria.com/how-to-zip-two-arrays-in-javascript/"

      ),

     ("URL+subject generic link",
      a85decode(r"""
6t(1K3Zpn4Be1A\3?U_$@j!N\1,9t-1-.6N3\W92.kiY20F\@YEc5eU+@fj\Gp#FbDKB`6+?
X:FEd9o_@V'FuDf.1FATU*F$<)(VC1Ums3ZqL;Gp$X9+EMI<AKYf-Df'P<AoDKr5>uJCFD,6
2+Ceht+E1b1F!,R<Ec6)5BHU_+A8cC,G@>bL%16*VATB@gB4Yt&3Zq'I3?V%)Bl"o(DfQsdD
Idd+Bk.Y[9kABe@:s.'8OPT^4>95l0f_Nd67k)^0eb193A<`N3C>P\/OMu^6o@7f1GL^?76k
KpASuR-DD#g<F?U-@9hA&J/QQG'F(oQ13Zp.00F\@VDf0Z.DKII0H#R=U+EV1>F>%TL@;0U@
%144fBOPq&ATU(XFCm*a%15I@DKKH-F=gI4@;^-uATB@kDI[TqBl7QE+E;OBFCeu7E,oZ1FC
AWpAISuK/PA*@@;0O08RuCMFD5iB3ZoS^4Yf#ED`od$EH=9>;FO&H==.WC<(0ng-?)+%-?21
D:JO=f$4R>UFEDJC3\N-pBQ@[%F)5c5D0%iq7:U7Q04nX4F"["""),

      "{{at|Fri, 09 Dec 2022 22:47:01 +0000}} "
      "[https://ahrenslooms.com/faqs/ Why do some looms fold?So they "
      "can pass through a doorway.]"

      ),

     ("URL+subject generic link, with markup",
      a85decode(r"""
6t(1K3ZqCEALnrY1E](s@j!N\1,9t,1HI?N3]&c<.kiY20F\@YEc5eU+@fj\Gp#FbDKB`6+?
X:FEd9o_@V'FuDf.1FATU*F$<)(VC1Ums3ZpRM<E)F>3'U8);f?Ma?Z0akATD-@2*tAY7VQ4
MDfp/5EcXB$6sjG4DI6mlDKBr;ARAke?YspqBO>144WlmP<E)F>3'U8)F'gX]='n*G3'BVa4
[Ck]1LFQtH"CE)4Yf#\1.>PLBOtO84WlmP<E)F>3'U8)D/XH+?Ys^lATDZO6S^ej0MH1uCNF
cB?WL`SDa-B-4[2qG7P-Sa;*T#,9is8/0JGXW1-IoWFD,*)?V+UIF(J]hEaa05?X[D^F`^tF
0NUCm6XO>AF*),6B4!eh1-IoZ1-[oE4[2qG7P-Sa;*R'(1.=,]?X[;eARTUdBl79hCh7*uEb
T#tFEq54ATD.#DJ=2U1.,DeAm]aqBk(g`8RF\F+?_qh<(8H!5>aXY@<Q3hAoDg4?Y"(sFCeu
i@<-:/DId*kH!b6'F`V+W1.>PLF`MA6DJ*<pAnGCl5<U,P5?1ZP/N>sl5A4V8Bl8$(Ec,H1?
Z^3nF('6'?Y+%b@rua*@qg%1?Z:%(@UW_^H!b9,DEUED4ZG,Y3B;1gE^)]04[2qG7P-Sa;*S
W#Ch[s4Bk(LZF`^u!F),K-B4#q&F`Li.Ec6,8A7]dgAoD]sFD,5mCghEsF$Df14[2qG7P-Sa
;*T.c1.,DcDfTDrAS,Og@qfLlFC/m'A7]RaD..]sF('6'?[6R4?ZU.&ARB:mDIn)V1.=Dj%1
6*VATB@gB4Yt&3Zq'I3?V%)Bl"o(DfQsdDIdd+Bk.Y[9kABe@:s.'8OPT^4>8ZM6nq(d6nL>
O1I3TL75ZhP3C5GW/MfCI6UX4076*.m1I,S^ASuR-DD#g<F?U-@9hA&J/QQG'F(oQ13Zp.00
F\@VDf0Z.DKII0H#R=U+EV1>F>%TL@;0U@%144fBOPq&ATU(XFCm*a%15I@DKKH-F=gI4@;^
-uATB@kDI[TqBl7QE+E;OBFCeu7E,oZ1FCAWpAISuK/PA*@@;0O08RuCMFD5iB3ZoS^4Y\WE
->u%$-?4)i:f9_O8Q[<O4]FjP<$lQI0eb:.EBR&m:.5U!%16cjFDu:^0/%NnG<I]MFD,5uF^
]<$BjkmB1.>\kD(faEDIn)H1,(I=04\X(0/579A8c%#/R^5HATW$1AM&%GAM%b;Eb-h6Ccr4
7ARfh&Bk(k!GqF,O@;[Z*/Tc.fE,Tr3E\2ETAH"""),

      "{{at|Tue, 13 Dec 2022 13:46:47 +0000}} "
      "https://www.theguardian.com/money/2022/dec/13/does-a-kettle-u"
      "se-more-electricity-than-a-tv-power-use Some older [WiFi rout"
      "ers] can consume as much as 18W (£53 a year). The more modern"
      " Linksys Velop MX5300 that I use draws about 10W, costing £29"
      ".78 a year in electricity per unit, of which I have four dott"
      "ed around my house. Turning off the internet to save electric"
      "ity probably isn’t realistic but asking your provider for the"
      " latest, more efficient model may save you some money."

      ),

     ("URL+subject+body generic link",
      a85decode(r"""
6t(1K3Zq.8DCcnc1E]:uDBL\g1,C%,3BAlK3\i]<.kiY20F\@YEc5eU+@fj\Gp#FbDKB`6+?
X:FEd9o_@V'FuDf.1FATU*F$<)(VC1Ums3Zq+7@r!3/BOr<-@rc:&F<G:>F(K0"%16*VATB@
gB4Yt&3Zq'I3?V%)Bl"o(DfQsdDIdd+Bk.Y[9kABe@:s.'8OPT^4@:hk76r^h3%[NX5t*@^6
prj`5rLYV/N>ID2+BGW1H.$I7R1TqASuR-DD#g<F?U-@9hA&J/QQG'F(oQ13Zp.00F\@VDf0
Z.DKII0H#R=U+EV1>F>%TL@;0U@%144fBOPq&ATU(XFCm*a%15I@DKKH-F=gI4@;^-uATB@k
DI[TqBl7QE+E;OBFCeu7E,oZ1FCAWpAISuK/PA*@@;0O08RuCMFD5iB3ZoS^4Y\cP->u%$-?
4)i:f9_O8Q[<O4]FjP<$lQI0f1a7EBR&m:.5U!%16cjFDu:^0/%HcBm;cr7<<QZ@r#Y#@q]:
gB4X4]7:U7Q04?Lj2`WZJ3=Q<)$>=O'E-"&n06M/HGWdfNF*(i#CLqa#BOPdkAN_e;@rH3;E
HPi6FD5Z2F"]@02)$m@BQ&)HFDiaJ@;BF+F*2M7/T5NCGqEqt%16ua/ST*DFCB&sAM%h4/R^
5?@<6*6F(96)E-*[PF`)7R"""),

      "{{at|Mon, 23 Jan 2023 09:10:29 +0000}} "
      "[https://unix.stackexchange.com/a/479309 "
      "Lock the script itself] "
      "https://unix.stackexchange.com/questions/48505/how-to-make-su"
      "re-only-one-instance-of-a-bash-script-runs/"

      ),

     ("URL-only Wikipedia link",
      a85decode(r'''
6t(1K3Zq.8DCcnc3$:t7Fs&Oo1,9t,2```K3\`?3.kiY20F\@YEc5eU+@fj\Gp#FbDKB`6+?
X:FEd9o_@V'FuDf.1FATU*F$<)(VC1Ums3Znk=<HD_l/O=#\DKIo^9.`.H9jqaP+D,P4+@0m
UEc5Z&%15g@F)tc&AM$JA3ZpOQ1,C[C5r(eZ2+0kj/Mop`74gep3(5DU7PHSd5t!Xu3AiQWB
4>FiF)PqKDImoR%15g$9gpX7ATDj+Df.TY0eP-h$:A`LFCf?3/Q@"7ANCrUAU&;ME,8rsDEA
:7+Cf(nEcYf64`tjY/N=1H6Z6jaASuTA<,uDbF(T!(/OaPeDe*R"B0%/TF`2A5A1_b@Bl8$$
@VfTb$<SlQ3Gi2=Cb84hASuU(FEoni+`';!1F@$'0ICd\4]#$F7S-]/Aj'*^=B$Vd4YS4&4\
edJ71BS5$>=O'E-"&n04f#a1.?%C1.?D$CM@a!A8,I81.?,%B.nICCM>FqARTY%?Xn"kD/X<
!D09Z:BlIm"'''),

      "{{at|Mon, 28 Nov 2022 17:30:11 +0000}} "
      "[[wikipedia:Least common multiple]]"

      ),

     ("URL+subject Wikipedia link",
      a85decode(r"""
6t(1K3Zq@0F=\Oh0H`bp@j!N\1,9t,0KLmF3\rW9.kiY20F\@YEc5eU+@fj\Gp#FbDKB`6+?
X:FEd9o_@V'FuDf.1FATU*F$<)(VC1Ums3Zpq8DJim'%16*VATB@gB4Yt&3Zq'I3?V%)Bl"o
(DfQsdDIdd+Bk.Y[9kABe@:s.'8OPT^4>K;Y6U<Xk3@us@0ek7:76!.V3B9Gb/M]^`2DR`k3
&F)\6U59nASuR-DD#g<F?U-@9hA&J/QQG'F(oQ13Zp.00F\@VDf0Z.DKII0H#R=U+EV1>F>%
TL@;0U@%144fBOPq&ATU(XFCm*a%15I@DKKH-F=gI4@;^-uATB@kDI[TqBl7QE+E;OBFCeu7
E,oZ1FCAWpAISuK/PA*@@;0O08RuCMFD5iB3ZoS^4Yo)FD`od$EH=9>;FO&H==.WC<(0ng-?
)+%-?21D:JO=f$4R>UFEDJC3\N-tDETaDD*9XCGA1i,E+NQo@6HA7DfTJDGA1i,01U/&FD,6
+"""),

      "{{at|Sat, 10 Dec 2022 10:05:35 +0000}} "
      "[[wikipedia:Gunther]] ''<q>Gunnar</q>''"

      ),

     ("URL+subject Instagram link",
      a85decode(r"""
6t(1K3Zpn4Be1A\3?U_$@j!N\1,9t,0KLmA3]/T6.kiY20F\@YEc5eU+@fj\Gp#FbDKB`6+?
X:FEd9o_@V'FuDf.1FATU*F$<)(VC1Ums3Zq+-@r,^s@j#9"D/`onF<GC<Df%.@Dg*=<F<G1
6Ch*t^<HD_l/O=#\DKIo^9.`.H9jqaP+D,P4+@0mUEc5Z&%15g@F)tc&AM$JA3ZpOS6UNUh2
*sY^7QE:]/MoCP2_@?^5t!:n1GD-R0L7Ka2*jPoB4>FiF)PqKDImoR%15g$9gpX7ATDj+Df.
TY0eP-h$:A`LFCf?3/Q@"7ANCrUAU&;ME,8rsDEA:7+Cf(nEcYf64`tjY/N=1H6Z6jaASuTA
<,uDbF(T!(/OaPeDe*R"B0%/TF`2A5A1_b@Bl8$$@VfTb$<SlQ3Gi2=Cb84hASuU(FEoni+`
';"1F@$'0ICd\4]#$F7S-]/Aj'*^=B$Vd4YS4&4\edJ71BS5$>=O'E-"&n06_Va4YfH?DKBo
.B6%Et4YfH9Df%.JAS#[26YnYmG]?Ah6u@3&5A=bOBPD!?1IOr*8o7=L<bkEE=ZnQ/"""),

      "{{at|Fri, 09 Dec 2022 10:00:50 +0000}} "
      "[https://www.instagram.com/reel/Cl6fxqKgDmy/ "
      "Leclerc compact loom/how it fold]"

      ),
     ))
def test_rewrites(description, email_bytes, expect_wikitext):
    expect_entry = ReadingListEntry.from_email_bytes(email_bytes)
    json_bytes = json.dumps(expect_entry.as_dict()).encode()
    actual_entry = ReadingListEntry.from_json_bytes(json_bytes)
    assert actual_entry == expect_entry
    actual_wikitext = actual_entry.as_wikitext()
    assert actual_wikitext == expect_wikitext
