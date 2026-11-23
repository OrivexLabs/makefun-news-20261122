#!/usr/bin/env python3
"""
Sum up 22 November's world news in one image.

Deterministic, offline generator: draws a one-page newspaper front page
summarising the world news of Sunday, 22 November 2026 and writes it to
/output/entry.png (override with the ENTRY_OUT environment variable, or
MAKEFUN_OUTPUT_DIR/entry.png when that is set).

Pure standard library: no Pillow in the grading sandbox, so the letterforms
for the frozen texts below are embedded as pre-rendered glyph bitmaps
(4-bit coverage, zlib-packed) and blitted by hand onto an RGB canvas that
is encoded as a PNG with zlib. Same frozen data + same code -> byte-
identical PNG on every run. News facts were compiled on 2026-11-23 from
that day's reports (Open Chronicle, KIRO 7 News, Standard Topic, The
Russell Record) and are frozen into this file.
"""

import base64
import binascii
import json
import os
import struct
import zlib

# --------------------------------------------------------------------------
# Canvas / palette
# --------------------------------------------------------------------------
W = H = 1024
MARGIN = 46
CONTENT_W = W - 2 * MARGIN

PAPER = (248, 245, 238)
INK = (18, 18, 18)
MUTED = (92, 88, 80)
ACCENT = (168, 32, 24)        # newspaper red
RULE = (30, 30, 30)
LIGHT_RULE = (196, 189, 172)
CHIP_BG = (238, 232, 219)
BODY_INK = (40, 40, 40)
CHIP_INK = (60, 50, 30)

# --------------------------------------------------------------------------
# Embedded glyph data: one packed payload per style. Each payload decodes
# to {"space_adv": int, "ag_h": int, "glyphs": {char: [advance_tenths,
# width, height, dx, dy, hex bitmap]}}; bitmaps are 4-bit coverage rows.
# --------------------------------------------------------------------------
GLYPH_BLOBS = {
    'masthead': 'c-rk;OY0*y68|nf`_O8==eDp5IRpYB5W*6IT9T8)9s&b_5c1vAZMWTeRF$f;GYJHXxs3n6ZcFuk$-iAb{v2ZdA*5d}AB54@OZf4JpDrJ?yIy|$->*Oa^zriHx68jSAO5SXy()KA>N;J;ikteCZu?p$&eFHnnmPDz;4K3#@_|nbytx%ijq$O>`ypIz+j!yg5bsu$K8~PA_`IFc-?%K;i0>xFW<hvB5|afR@#B694h!u5M#*HsO8hKpF8BfQm)94KS>Rt3pKlx%<l}V<g9W<Su3@lXDacWXwIzt30JTX3@g1a=3YYx3Iy}jOjrg%4F2#cF@22>FA*2Q)z5wkI$b#*Bp;I-S1<Q?CmNYy4N+9uxr642gU9)gQB*8C@C<{DzD2uWngG4Kcuyn+a6G`N`{oK;N!xbNI+FHv(FQlnC*MbUR&w_->U@4@&`VihuDWtjj(m?owh6Qsbj6kuWxNTu}JJWLvu8}I^mr82$Vudb0Xjlfw>3kM{`TlzO_cN|g+dpv?=6Z>c7UY~_@J3QDxO-+XCF!+W;~Wa^XH3M>s$o7<B+3pU_VeV@rh*(ZiQNRTkk5I5o#x}!Ner+hco|_Qm3uwMu%#UrBkbIJEfiZAgEYhz?o*DiqO;pLws#@~Hnh4-U<*AKBW!m#0^7N50;}4fhKDtu39COP_6!}m41~bi6MXBUUY6{P<t(0%-^|wwc|zap2|Z4H`=I)W3dP3$a}4`3QCW_#2UHF0uZ|G3P}c07wZ>RixQv$zSp86<Lqx;#Z>xjT9ACKldrPOY;<=zdZhrbdo1a$Gb^9lGKb>yll`A_+<3|3uij+*{oA>4Y>ZI@Q$U_;bb2btenYh5jStd?1agvD>YY@f3O`}-l)8oRjaB!Rd=HN6F=a{&Kz_shI!exJ~%sfY6;w%%Vm^d!qCS&d2B7bLb=9%OTaQ>N{4shw|_Gp~o#8tceb8wCmPwlQnF>v`6Y=HLpZlc5T@P2aW2lu#)<3F~TjETGZvoBVEriHxfkw4RD{<@yv{1e@obM$r(42)Y+<KF$Az#1ss>yofV@Z|T1;KKBN;{C)w=?QB6eNUveT<exM2j5S;pE&sh;Ri+M2en&pU+a5cYsFs?0c_F7m(Ofk9MMN)c9$kLu*;`&3@-u@&F?5aNd)}{zJYJx8;AoVqv-z3dIbk)IPI6c4w6{F{Q8^*DpvJ=&$vAYn2yFa37m^oUEv;0vFw_5@2*f!%&c2Z%yfF@0>z_}{MDX$D|1!)DuGEdp{!qG%Iiu?u$pj3!YticqJv%B?2%&!2@J%%u*n-Gl`aDIcECa$?FdzT+v^1qZpM1J?^<>gj)26q@|OFy#=?lEUSX4In?qpRCbYvG3mG}cruPL6O0@4vO;Zi+1k0*j2U`?dG06|cl2q08O7x6T**liye~`{f*+*A5irO_5eBWmzh_aO3WJF2I@vkr(ek*6Q&Y*9_uJU+-MJ&UiG#Jg;i8!}!e~KpO=xt8%Ql5|#SIVFs$)E;W$B-j=wZh#g-H`)kx_VYC(gTl2cXh6N^oCT+fHsE#1CjS{mYLAw-uycJ<<Or3M#Pu>E@yo(xCX(6Sb}~hwzO60C`V}}rM55UnH@wc*s<q;q>wuFzSvT^q+GM`n4f-L383%%buo8N*6G)GtS@nTrgR3L`ck93x$Dns$_eJZ&rwDui{Qk@(&Oa~r2m#Nc|>AHix~kd#>|LfWB7phMGTK^2*Vr1E@5~L){#CP{_K9vp7$(06XMGdyvEEt(#K7${Uq@ckEuGmkY<5LddJoGY^D=<(1781Cuslo(D%spmyh$#gNq#<eQZB#Nz*@)Gw{H?DtWB{;P2tovt;G|iHH(Fdq~`_0p-o(5fLoU#R&GyvbQ&ksH2%OroI;?=$fcwdsPz^tr-NEsAy%qyv^`Xv)Oia<+7}-o5?d_h#GmbqkH5#!Z-IT?iKZKo)vX@#0iWl$1{-se9*1texC(2rpW8;w(i3a4@wqwrZyIDbA=5W#!$aQ-5Bb2s2xMi4%K6*-l1{~l{<7EL&XlA#?U*g8EM3zz~tjR%=6yRH}nmCL;nnvb?w%;u1lR3Z=rY*%T)gybn~d+t{&Bx>1y<T<9qd}(6fVk(#`bt|NR0RQX6{E?do!@E(O!Xm7HtjFV}m-h-7T-v0?K9Oh)q=Dgdf_yEAbH1LUuJxIROLN92}CyR+0l@q5b>+}YeFc10lP;DT%Fb7u(`PZJWfsurHG@L9oWeQ00nuo|leYnWALp#g!1i`8X5>S}OXrPjl!I@R0tc%3*PQMRu3rHKN$=taEJ69?AWp&Q<tyyafT(ha;Kn>ulRXiUeS8Ogc(JKzi41hGgCE?bVx4{_<vwjeoqmmoh?wmI9KHHPkgJ@h2)-_%?q)TrN?>+DcJX(ehh2E6%SUo1Z~t`-sE-m)#FuCN)E)mDV(6y-FgD>N_`<aI>jsqAFk4<34prxH}90!(A9R6f_AOSG|_5$EiN{vFJ!LC0|;e=?)G&Rxp;!u8%6nTyrXg|5*V6jIU;%rGnBLN>9^U=Rike#pgRjy_Q3Ip_=?`-2(8E(z-?Mxvkyn8t|7`S90%B(~9=jN>pYVx;ziAiCnX!}b=(5#UVrE4w#uG4yxO?v)wMd1|-}ZO)-}dxPY*<qOX}3w!jWQh0n^G}a*+s7AvisrjL;qk7`yvg1czX>7u8fvIpJL*>q7*p7RNFn-n7YS>~#xN{L<suol%$Yn5d8X#krFtsbGDAB+fqT)h@h&>h65e&^^7ZS1f8K$CnMv7u&Q+EE7zl73I(cT4<{5h(kJ(KTER?RVxw>@HwOoPlyfa{+nTX>d|o+5!gWMHJhk?A(y=r@{;E}C9sF=v|#ZDv=upE5Fn5de>Lf`Pt#|NHNM07)wZe*',
    'top_kicker': 'c-oa!O>5jR5dAMcyC7MzZ0)U~9~4Skdg-B*AWNF$&_f_lC?Ws7^JXOPCfPJZEbC``H1j<3W^^~)-lSYFQ~5I-{4x&d>hgLx*f0)PzyID`-wubn;mvUPIWOZpy3vf*j)NznDt|`S@M|32vXPzKXea#4=*I!C7NX6xm8n*%&{0Vg6t5I#%8CnlQ)vS9@SbP^juefVsQ_2f<?y6tUX@l@CcF)7WGl_UeD$Go+$e(PMW<<nDQISRt9A2WSi~Ri&v0sNVfqR=LWiy}_pCH(=-Uc#vt?$kK_(pbr!;q4{$lk|^P(Aicb-};+pNherAju{+fw<9o8y&eYS7Xijw3Hm;Upy5wrUjy<nTcVM3%sy_8!zMQ!@{<hUH}&mhZtj#m7ijHhsrtUfR(-$30pCoe!X6{1~6G+4`2WdpQSmt=)L}ukm951|Pw|ad3C4cApAYOJyBJRI2{Kv8?pM0*PxwtZ9~7^zLB6L(`@=h};zLoSNB|nfb)ev{@`}*mY#r6BKX^T7@d;)Vxkg`4dy-4tFOxTVMQP<L5Kkenq-o37Rr?v4Fvsvz;NyB4Pz=Mg?-qcbFtk0$G`%Lm49qc_^$MI;vBH-0874I92KpUDhFw7P6rB^;sck_vo$@A)s2^y74H4$X&P#0l@7-V8NW;gx$;mbRk5{xOsQIo&-&%3!$Xm%-^1A=33Z6p8=%}246)7IziK8<Yl($jyBI~S?!B$-4W<~e`X@{U<_RllD^}tbH`EUAB?hQyX?c+wP@U1z6ahQ0EJxLrTdNhFhq6bu=oLLfzuTB;$~D%8d`#uC^d*$-VG-i&Ks_Nm7zOZl+RM$_%fkKGe`6kR~DowF>;OgX6DO&%57-*!ltu!Ih+-~$ic`CP}W4No`;bN#tI*NLJdN|x3WUoDcFu_C>9yNzyAm1fG)!',
    'date_line': 'c-qBQ$&MUF5dD|BaH&J?%X|bExEW;SI)h|jgs~;d^1t&UBCDzydoYYZRJW?5x*{`PM7~%)Zf_q;8?Q@$zukGeZ{_~=!*-|RzTLn1@c8g{yZg9(v)#S2VYj>6)$aFA&8$XJ9pAY9xNke&V=cYcyAJziXTn#dpt~jo1qH3buGOyX+C!P#M+-_R-Fx&I`YH{B=Zt%=5R{!!)Bm_e!2?UZ+8IP@*MFDZwHEtXNM&fTQCM3qy9CTU3yd_)=rQEkXbT25oeFH)Pp{;P(~4k5T|)1g1vjb)VPts~7F=b=5>y+3FRSLdG64%;0;WP6J<*<N7N5wVWw%2!@KqmMwk1%|>KFysXY0Yo0c3++@j%ks5wS8@nq@f_D8O|j*kGO1N6(rg_ALRkao2``X#y5zKio56u5)0yaQsC!Voqewfe=}OyJSsHEg8T5lvV5cl+DQgkP(Y~%Bqh`c5@nn{2f6y2jnA`v5he*pJtmS_)y_K%nAI0qdtyS8;WyQ=M_dv?ufPyrOy_RM`c3q=2SIUCzPQ`R|M6r@MI8Wln`Q_#1|b~2c9Ur{GK2qlWriVd0xhXFmX2G4cpZO{lN1-$OO3@jMYS1wI_<QEi0A4_~u>W=t`E?ac+|*c@ZlDFi9*kIco~UWkAHl+mJ#Z!Nry)yf;j6-3C{px<KSzQ!R3Ub(r}}K^MfHnAj4s1dofKp)fQ(^N}L;63$m#jy#m%s|%y6+Kp^TnEFjBQvr2MKdB<_Yf?bwMUuj-&esO1b>Xbj!pS(D5!QxVX}wKY(RoFeU3_Sjc8;{On~ork8;IxG89KXk99^WutXyNTITa0dKAD4*#mwUPvg@r<#|nq~WJkxLaXq1((L6Xh_fMk3rcviwa0{<zyzGM>w|@O?uOlIAWqIBF6=O<qpVgux3buEJ_i~`s(Ig&TN~#PFSO_(FVukPoCWSdbA<F+$AWT02lQX+HA=MF*`0@FN7QA`7pp54~wBTp*+9%e>+0en1hCIQ+S+t>`O0U#X6B<h+pUAmEB@>-jJd`t=Nsx0}{@0!e;xE_1TnJat`+pGhU%!+l7MadXd8J9a(!{Uw1yU}CqHJ8!nM8T5i0F4xCwZ2jo!d&2$3JrrmTSL?R^--x)u9&^Ewtfd!>_ZOF#QHh!S3NE`lbyEeM!(vT(}M2ueHzJX+sQ~ud<ipl;~=jJgOt5fbxgtDWg=P^j=A9+e9DdK4@c=@rJ8bvBfOPbkrV~;WEv3y?QqHyNs>eWfgv4ZgGTr(3}J66Xgu$M24>C?nXK~Mkif|jJ)qY<7VwrqwEWW1pYEb`m|gVagbJu*(%}hC3ZK|Tn!e~U(+h3BU6s2<~+C+Ynqe%$}822JkcA`pb^IRd`y<dv>RpSBg-Ey%kGI~=Vel-mc<4PS>|{}vdp>AI1AvX70XDrv<AwayCe(Xtf3BTj`7x>LwFH=jdCP^c`8sRQGa-c{iCpzK8A*rtxi?v()sl14<?{Mdj',
    'kicker': 'c-qZZ+m0MH5dD{a?gwAm?e@NL2XPe;Ap}w6Yx2NDqzEJw<=;7VaqnbjLRbkTyrb2b?y`NV>QveDdU^FS*ZwTGKbE^KtV@3W?8S0tfu8^N=gSwbmb=%>y4?MOcYfVgyIQ|4Z3KKw_eV9$({=d(2G;JYb@VZ?Tnt7TV>2>r?;|PRN9tX18Cy{!n9wUV$;OVZCc&7>Mz#+giA`F;V52g2vTQJdi6eZ#XdjhV*kD97Kb$lTGhNvej9#O~<eGEoqZo3{m@tMD<W6*8!6p>SoY4T~EodBy;wa~{Jng!d-CFic=cAiZi?xFf^R8pG)<?Cpb4LI`<1nTVe(ho9hj=Sq4s#1%+RVAG?nIK;tcbNS8GBXP3$ZPoW5P5)z8$q*4@V(y1=Fw)`)l*)8Vw{OY7EjDjX3HRN)#cTvCmbSy<C}smYmS}gy@)fl|;%3)1h%_5=9lakPLs$aPOTVcIBKqn9ir5la4iAk#XnB=OVX&E;WtK-x@yzMBp=uhYJr>L>X*((<-FQl5#{vW^d_K!b62zt0)k`U2J?tu6E2ljHGTS6%m__o}YWMjD$lFnxEfNQ4p2Ke~xqj_1363;^S8#I$z9|c0uO7ADZ~(^us>z!%<K~zKt3bK`XUIutJ>-_o7`1DIePI0ML1Yz(i?sGtHH)8S)PI-D#UTplTs%UtLS_5n6gA5V`u9k&Os^O|kJ_r8ui$lfE;c5SEP}j9cR_&<JPJR_%rG4qe)j8T($~>CV`ej=o?8#}Rrpg55yhRZNle6Cb0Qi8qRL5t`rJl46rXgCrIw>fI{JQazC<bt}jocqj-*mlZ_kjv_ovf~ZCmQ6Ln>AyWMI-35GDbKjb~pDi0fXl526R1wYsE+d@<jIMiuv%9b{?VP)50b7x!?$y{d&@pi6G4S0x`fjg*^-$5z(E>yw2?Pa!nmv&|%Y2MNL2b78(aUDu+kqz{I^W-_LpfcY@}Zc`wr<-v?&~GpKaHntJ=<}byJargS$rqMB(_@h(`R;?sQoY_WiJv+v1BJH-X&K~C-+Q~Tcm7G?~tG#y+FrjpY(AP5`CLyu83x}ft#&z(pdCZy&|}5OZN#r35eQ{(jp{>%&g9qno=qFf})OZ9RvRnA~sLn%Ao{G`vn!;zXl8EUayEd<;fXovWRb|^NL)ysY!;2+D}9+fY*LflNBmoI0ODC)=B5GItDeWN}14eFw(Wr;tEO^QCNAoo+dPqs#n_#quS}SvCinyi-rf2sEx9DfPL(FHqi*+N0J7DT^RJHCki@BlWSv|vdAn676Q5T^R+a0k<muss2m6i7k#(nrqu^k;)nJZr|#0d8f};3O;6azLZbHT@7O4UU+^pa+4WeL5S;$jm?o`Wh$g@V!|f6`C$GOFF5o%-2dYvJoUtAr90}(%WdNnPL@mL6J7oCf>6<ry0U^Vm;{',
    'lead_head': 'c-rk-ORFWf5&kb{eHN{^G}~nFECODHVDxHFh)o722?XQ+p4PicQlA?SF*uXk7;|n_OD$D>^_1qP$LCMh$M0<T=i>t*;`y-OfA{h6fgjJu_dopW)5p(`4?jJ~<HMgQJDx;8um7_rA<xHAA05wA9ODt;JRya;^Mn+V20%&~04V%Cqf?0DBsmD4Cr$NE`SmG;@u~|W7`=26Py85u&XmWWpAS|sLrKC6shDBXI3HpR-YQzZfX6%5iBSuo3OXXML`U+Xe4&y;loe`a23?44`toYX#Mm}z%J}OS^QJ?&j6cvb-ULs<v_mvf1S2=2J$Q?XGT4(&YZ46#j4Z_H1OY^Q$*#~XMc-j{nF6m<7Ao7V-tS&Lr)dk39}Li|m<5AUVV!ugc}_;5SX|Y|MYIQofJ)$tb;A{CNyvG_l5=U#A$W|rP(DC~vKe48IL*sM35~zI(8w5l((J(~@?Zzy%9b(S8N~?{>x}kL(L(A{qSI1HWy6pjuaMP!BJL`WmFWVKvdTPCM=c7t#A%y&FyIo8#vMM7BV0UF&2i>wM;qq&u|8G5C)x0-M&pLn%*XF|=G<6J1N94D4IcKFjx#UTqF(HQzu5b&%%~RagLeIxZMG4~vPj!ks+WzMfeAkAHmQ_`jdAm;Zt7<YW)ERT%+A<VQV3}RTEPg=XM?zcCedxhYRQ^?{l3~4Bk8{*+ZUat$xeT)mbh@PPt<fln^#I3-(Q%ORb)<7UA7}Tc8?hyFB7}-^`6}b)j$_^gQ~e<3y8XvU8C;F_v|A87qDSNTiCFnIc(U~a>ET98q7WWjnQv>`;C>`*ZWqlrFJLO_);bOwL&cnm<zl5Wpe{2kKEJ5W*$cg+0p}fg&N&lBDpuB({b#|ff0Hm>CU+wge*=kS@t){vc(lP=_Ybg(bBmq+AhO|$KSTtRh5+oEv~>`<E$HV6myOe<0No|D(D#%bcZ#0P;0yhWXM16k{vyab&8xL>2yoh44|xfq?jZknkDdk1Zr^tnar{A5&9<bwKD21+SX;YG|Jxa)m!|x=D*7X+WI8$7@Peu_J(}ghv-(muG^;ACIza`WahZq!?fE(Y=Dnu-s(23E&$x%v#nW7_%4eJ!$fKbNA_XSg1E!>W!PfVLhtM|+4Ub%eWuBis$|zCVzVV+n-;L?&e4p5rMoDlYC6%~mw;dq5lR8ErWY~9>YQxDf(g{bQUJ#jOM*Z5qjoF}a5J$g<m840(TZ7cftaOsf`a00d7oHZydlTRO1hL}V=Bw@wX&L1oui+Dzz$BW=|hjII5Pe*MaCnWPq!d`zIfuBTyJy=@}ebV@_H_n+nBi=J0d?^M+E(jnX59F+;C;$#^Z*|6F1y(>E$4$xZ@sDuFi8?kiB#Nuen5?o32RhcSU5Ja+gkwzT>dXZ!g>A@_2GNY!iD*`l2<Eax4Zu9o)7bz+H9H*{8G`iyXI4DlrYtWeDyd!uC&UD6&oY2iB^Q=L@@f4onbHE^Ow051YKGgn1pGvS5%qdHgYsJ~TI5*om7c24!KjhuRZ2doF1JU%NvN4{o|;QwAxJ$n^vpJ?Fa-iv0Q`!r@^~E-etb1g>5c0mprti52nLwv$jKX7_ouDFay_F7jxx?|sF*C_ljCV0U#k%~Q~NkR#jL<Svf3xpduY6S{G8>l<o6HaVJ3h~&2M*jGt+p?3!25LZu!<$dRJz`O_Jox!$k`T1*m7q-+Ja@(;*Kn#n5_jP$;s=3a*@w8dONVd6DQ8#b%r3$jh6Rg^2GkU_@F|h6Aho-}ytHL;P$AC+1eMqfCZ^d%<fvfwA>Leq~p;R|E0egsv7%|u?)nKcqTLb(8DsQ_0RPLupL`Mav8G$o|rC&w+FM_FZ?M~5NMjpF&>uUOM3hYCTH=3_<J;c%6N@}b3tpSw}nS@ORq~XJ5@}%XMw0!U<F-XhTN0kft_@#?+9HP|bZE3YSE@Q9UY{Rr{M#{USNb`PngpOEEC=Q!0KM4h*sCKpH-At^cD#I)NZV%ajhtI*Xi<z%3TdscDZJe*z95~jVJLSN$T}50v0Ccd4Uo<6JDrIuHU;FGyPal(>gnUw-T6pAXo{xss*@dWz2Y=(={#WSk3+Tf5%P}>~+S+YVp%-Vcg$N{HT&=B@H>X5I5QE@4VLKVEKa9m8y1Sv<cRHra=EwXcbm7_`YP843Ia^X+GK;@lW<jWa657ooS)28(Nu7^sYvh5){Q(4TNH0gb)dz4Ny*R$$fu@Pg(S9|*byt^x;h!Y6{Iz*2@us(W;jV7|!&k{*P(YAD@~wneT3UE2ISN(8xV%>{V3G5R_26V;T&M?S`(RK+AB=QptvCC~C*5%!LHz8wE5n_0=(N4l3C?+7X~yuGT=(X^80<&sV1ogP4KQ$q4`t<H3A0g@J#JiC@*cyNsnIUKbja=SUkCJNDw)j>$eSJ6n?+C^X%9c`-+%uXf47?nSN1?aI+@h+W9krV_GD`0$PP3HcuqQMrYBRLUE9wM1?K1($YoBXC(<5*D}Xk&gIS>gFGVXTkqu5)qC(pV1DVl?kZnM2iy#XxOTaXCliC<~x+h=0biBXx+kOe<TCzbuHD-0_z6vE?4mNQHI(4p2{x)uj;wrLMGTzGhN<b}-phu397oG);0N#s#)f+l~>@4A4EoP$HdKH+-;c~9k<rGGsS}Bqpkuq2yig77&eUt3w+<qOcQ@3?)cSPbyS!1{PAtecB!tyj5$xG0<&#eJ(B<TKp0`+FP36?b4dvCN3sW-}4y*7D*4uM2h0fN=-!ixrUxa%CX@ulUFG+?^y9uL!p|C%m8_b*TMo=8me&_Mr-=;mgAeX|~Mvwk|$Rk!Dze8fywBfgQAp(`mZ2svaqY(`f%Old#3ez%+4T$v=>3mU&QddFw<=xzmU9;vDO`8lOx$~=k09xVeudRI>2If&V;<az#z$-?F{pJcE#f4mZGmT?=p!(#>btYNzT9hUBMZrXv{D&u;kIVVr*<{d$cuXhk^Jn>ysQvJVG0X6)c9tuxy7(H@sSMCS3i|RD*ROfg?36mk;VOMicm`dZa_>5?B{(F+MU|G&Go$!fvFU{aP{CV?p$uYO!<};<%?9)I`a{8AF@*qOA&j0n$r3w8N{5}7(0Jgu$c!taH3AnZdP9dagfjsH$AEUyjEk1O)a(L*&Q$GgWxh4i)=R{3c_RjbZ7~+nh7RCWjkP)L*lI*fp2N@EWhDUDSfNQBI`sXX6)I1d2wGkIee*XF2Pjo<q',
    'lead_body': 'c-qZZ$*$c*5dD|CVRMCg9^OZ=f)zqhj|pOm2n0n@{+&}*-L{h#Lc%00>)vX+y6e<jetmoKytMJ8^q02>pYFHv^vSc^g9i2V`&ZAOy|_KRzI}Fk_}Zzvx%<1mhx@JLYOS_fZ{OT+cf7?;%Wr9;nuBiJRj8_YMNFS>CbO9I?6~Qb!Yi%gUE_tjD-xiTifxSQK&UcXN_~2z{LEPEKD4S+)4Mo>8l5O*XV$YaiGMQ-lWMjLd11J0g9IaodF7Z{cY2vw@L&)DaEeu|i`jq`0oDST@U{TXhF!Vin7GhRlRKZENC&?1bVBHbLg_Xv6J`lie#kDIQ}rUUFx#;-g0P(U@?)+m6U2vYZZhgUZ*!~nUF#KX`+_v{aFIPUb8};LGhos6xu^>eFG3YYSr}1_7f}UfTnkl6)xBWGy?~18TqxM&T-edh1#DT*1<Y_+*f9es^Cc-`(o%-wD$Voqj_lTEr9Z3QcF_N7LCSpf*fSosk}J&gUoG5DCQ3a$hTaaa2<k#BojJ+s95vU0oa3Ffk6y!4rtAbV6rYOX6M=wK8<jOihUXC5B!1uHHBUqsyE!A{5cR|}d-C3OqWj>iAzIJI88ztn7(`d5fiT3L^Niqy*cO#(BN4Pl(3I!gKA>sv^kP_aiD@8y6N9rOL*T|G;?yCSpB=dSwiWg!hE>*iobe*VvVHocB6@)EToKn^_YtJ6Fr_8ZjFCbbl$)8u3EAP6F(BP-sQDz*TTd^%sFR-47^EF=Q67b)IhGbd68Lcee^~HR&Knt@eY@&egJHUq^MJ?mQqK2P@HEKfE(XU5ob$06Hf0D!3OpC%xT0-JEesc1x;83#Bn2fcfqO(DQO$<gypt!N`b*-TzT-UBpBz$56o+iX6^@}WPb2r!^yR(2$#3y4hwurG9G$y3q>Y|+ns(cX8l3N8ClcqEv{Z%Wv^+!LpIurTwR2B3(>;o^KcGD1q6Vaydx9$(C~g;Rnk1eA)7tSjDFXW~jU|zq+yT{wYBn7E;hXjS?vn1Gt}l1#x>9a5c?Lo=WjZU5D!x)bO_VDyRI^g3){cE1r-Ynb!73EoWeDu|kM(sQf3v<nkiHSy!!a48X)xR%I1r<V8mdkWHExEUVnt9VPDn3f0Af!(X(UZChAoVec;#G|e`!r>{CEk|Q;j41(g(xO|3l&T)B6gYPJ0f-;8y}$aG6X|5njcMdg>~42IJkzZjfjBD_7p*1WWZYdlXRWAuNr1CINc>PVxd!7U!~COOJqaSOv9Xor<w~Sp@)=j_*(>Ut7fq16Yg8%I=Wyaj8RKe+Jk{L)ms9pr!!<XjTyr&F+%|O*Vh{myUh$zW&YAN9L@o0o@S#cNtHc+XDmV@+d)Sro{w5`<lf}><4r+vmI%FIKaCRg_P!5YB@a{2Jy?$aV#K2g22VsP{HRe6K$T^8*X^&PkudH-_9O^Cy&l^%CC<zAWOZ+-(RN6L1Cbi=IX|@MtTdqa;uS90`YPi`^<p4nhs7{bEBr}CgWS66GcF!lIVy-%f}2kB<|d_2=Zm_WcF82>v4CqF#9oUjWzcZpx^eC91cL@=(x(qz;tR@JfDx^?a0P@aI>^@6v1)Rj7Yoiuy&deRjESap;0ZXhyz9zr)uD~6W=NfzZXx_%s>&9p4~Hnt+-Y`a{$FL;?{r%v&qOvjaL`D`nT<x54*BWr9^OqNS+k3tD)&;*|koJGPl|4nn!!nBkjCg-@iO6*F7`T^HZc9L##w3r9|1B7(B8*68p`Y-vQh+0?7',
    'chip': 'c-pO2TW%aj47|&H&qu$fTZhO662s^R+X~<$h7}ty4BtIf?46M;IfxRZA?$E>nq-kIlKQ$me5hUC*713}3&+0IcW>{vJDc|H-TN;e?jN?hubbKKelBq@yLG$S!@e04yNqIt33Cpa&6qy3aWcJ~(;3s|;pfErGD}b)&w2^htLyTmZi3KYrD?dx#%yo)&AkM0;B8f9-WTgcg0TWqdT5UaHlser?0kAWEsX;-pI&Csi-SSn#5rZ))HK&=1n?68Sm$?Z3BeLVpFoQ<r-j%qQD!*Bsy<Z=eWp{4bDSdJ=Tr1k+)Xrf7P*Ot;1rR&^8!PimeA_TjWtM**^e_f#cGO2?h2x|Xxt64VuFp(gaHO7A%{RIP0<uY7Phz1W((#R(wy%j(OqLEOjxzJCF08Y4}>(NdkB5hfw((k2avQ1gwJ)k&GO`zbtgirm!*{ygpy(05Fp}5I%tir_?}C72ubIWK&ik1NtuFt`gMbEgR;?m_Z#kI=23NLZL8`<r1B2o$jQws{pbxLHIFH|$goB^ShOYbaa80KB;)B`UGfO|QAVOxtrJ=%-6&2k6JFx6rzasJsKPSUgo+6{Gx?>#Yc$HS*L>3W{lBa!0z@sqZ|S1d5l7PauDvu#_T%*e5&Q}Sm_Gg~fL!Bp_ji9(eE$Q*fBd83Z;Uyjoi%J0uFse>rCq9JbOS`mf{IttmOr6Gz#yY>W@e8gtuH2ZCCq>RMohn7b$EpI|K?iV{PEa87iTdGq_h7b24mHUKInn-)30voI?A0kYkm9;_p*i%PhB0}w0A6eeT2W1z}?5FvILGtL5qv0nR?Cah4tkpEj_&GwS4OljM}VSBSct6V981%TGw=ple;!#^t0>ylC-QXW56V1%aDN)sb2oPdd<R3q#G&PFNI)mBF0zGo-1rEvKOCKr?ph<q$VTM?5F3|)v>@a@;V`{iPRYidfj6lVNJ0Pg|y}Jq?^yr_d!!IoHRP!m2y_M6eH)V;p(v@^T70}YZ}3iE=~lbT5938E6rHdr@JqgJL{Lfs=21Wpk|fg>PmOuf!9u7SP`3+zdB>nwFVGX#^q%#ap;`${8(!o%4!kMcH8VU*VZs4u3tVm7c#+lBq9SE{-tqkU2z57B#5sSPk!_vs+m!$CwIW%wC>pN?`&_reftYY3V|5',
    'head': 'c-qxkNv|YF5&kcI;nIi7J@auwAQ=#g#3ByJvT~~#gn<zQmW<{9PR5d3b$cW)Gqy`luPdV~Gb3aDBC5Z*y?qmN{UnypZZFo{Z}HV9uWv6>-EXfx{rt`Ax3`xsZa=xb{ME_3zT3OJyZf!4r%Y!(!kG_y#zUX(5T`kAAKz~;?OE^c<}PG=xc$4ST-}k*^Hlgx!tmK8pF9UE{*+d<chUZEMR?R7^eq1;%2!>sl(uJM`_%Y+8-(+;ZO^kxxc7%jz?Khfh`au*?JB&#i*Oh2e!#JLu{IN?t{1GFH;Oqc^0izkxkd`>iBBsVsV*d6>0D-#N}FOEDGiEl$2bIRAUi1*{7+}YOOTj#Bb6?Ob6%QAIUBrSW<-kWhf~0sz!TF4@Y2s-W8c~F+1=^H;BQEp7pt_XN74Sgi`If@MHj8GvD8{}@&*=iZBBN^*jV9A%h6;znO#Mh9WXYSJc82~h4_o)12QwORdCP7*ZKSUQlnsoGF(FbhKNF<6?jKkK$UhmA3cfZuQ_^+V){iF6aJwEI#ym2Q?ztk0kmXnXv?u<na*tNH-mCywyjC&N12p^Eo-6hw1tvLw+n@3_ReS0!#d@<mw4dEu^A1Dsw7-GyQRYiev&1Wy?h=EK(rq<(aJ-za}NtVOvqq@DOjGY%TyA%jGLAr0+RG*8%WBlH6BG@4Q3oG?4+w%KC#4&r1`XNwNLbTx$P+VezDR{(sj)2q~(l*v`AuER}XoqF4|wRXyq~Dre`kM3+NVg7g0#U_uIuTY!}6cqAk~;B?^w=1M)(0k*i#~(DEWb5cRJhKpZV4PEiXEv{gZv92p4ij_>oX^V0b{6&&E#Z~%2cPG8(GuNg|L_8*qS_<`=F;QPjWw&Z+}ud^q2f{zANOyc|;AcQA7BF%5$h)&`8+$D$)bg<}rz=un0_(2jbF59%bXN`6*c0#NpW5H!zEyJd#m4o1Z3voo7yVTb>GN6&#V#&luU@|?PEGSIYI`d(eO!+x5ry4*))MOUA?{?@;v(mw$5nq*Ztn_X`rlqcpuIP-p9y^_YtOASL=`f11iYpy4PYuTd9i^cj>A-3_9_gR~z0#XJ5rWB@r+M}`1VV_Gy<)_o-#x-*vhz5+36i+5=kRCPWh60n24+Z~5Cn?YNIIW`|4zcV;x|%9pDPJjZ^pTjP~Leb2}qD(BO%y0<3?hfv60B?b`s{>3kf(@bb2eMQ>nh_jCG1b$nQH?@f%o?E@AHVJ&ZIERK3xzi75#NTO`7M=O^wbTNuXM51`D7TY)3*S4@IQaf2j?HXbN7JUsKb&f{K?Fh(^*g`L}Zj>PDGE-0HC_|@9xjwwLEEFalp@gE*-)K5S?1lbX_ixV0RkFn!iGpr3EPEzTK?_E!+@g0){fUF{q9g@_Z8Axb$)frFpTg;{VG6mO3dN|dS8ex(|<*5rsgL4-(xXQgKXzBvd{t-mmqP0+qjY^*@3Kl|FD{`!H2~^tF_pEaT3u}g&sBAWoHU~>QwYUucP_g)5lMM03pn@f5Q#}`qDjb$Gx@)(|MTa=8PKPp!yawrQe=I`O%1#?s&fIX84QNo&bbI>KV{X6XvgVN0Sz|n9JnM4xd6TuPKJFp8TDx0G{4qg-;XiU~j-V`t;QsvRh-TIZlq_1ln{~lV7Iuju9H)P%q*X4K$}Y9Q6kkV<s4T3KW-U-)4Vh}s8)(HPm$S~^lk^E12EEb+(f$RJg+1=l4$*R+Ub{>f92&o}&LH90@?}AGmXKc9m*hE2H4n`z#zaHas>g0Td*V8{mr$~^(%{w7X2SisxnxIotq_E&nYWCis7A{`Y(*)yrei5}tAK4C<?>lPL%a$YXCckR*{@mhc|7+*U5wVAJ};Gc8r`j}`9u1vBT(f_r!b6#{iUi`*E>*X>@|{tGU=fH=YhGcX`b?YwhF)z?vykuMz1j0UI#itY^FhDvRY|qKsk>d6LexVzKLTHAjgNytNBuMK=9;&=hU--rp}dRBUGEf)he&AF_PQJ#L{B2;!$$8sRf*-&nqaGK5{tUF8ElFkw$A<zndfa>?4mEc-g^n05DJoB7!y^1YD9~HD(ZrXd)4-8YxBMQw9)>@eR*|Q^K?mK+1*sQY?LHF^#w)mJqW%kS0RVi_v07HG~MhqC$pNBbMQ1Q<ngBJ@0GhZ#YWbg`mNiNF(SZ4st7u;LLW+^Bk>cl=(C?DjY$_D1X(HfxVDM`doLwFFkhkNWd+S79X%m0Fl(^>azHlpg7?h?jX}Dcti{TA}$@-jQ~K10R{@(CXLrIvE>lY#c`q2kU~gU-hjU+CxEw;-iL(YTi7as?+M)m05oW#qM(E#R_bFzwi#cDE1@;9wOZD<zlptcYH~&ocr^o=JV2z!Ftf+kH3E)=u2CRNO6atJZ&i{@qBw8HsVZidZ4k+@xQzoeo!CWWE!{UkQd>Z=TYLxhF}f^pT&;cPaA?jw23k0kwbwN5RbR|Qf=?}8+6DkII8m#=B!IIZo7dd~%}}bYdoNgi%b~jrA@XF`hovM=27RvLW<g(y{bm`K_c<if@oSCoH+l={7Q44Oa&6$|0=_13F{my~`CWXNI=UWzfB$-W93pzL^IJvl;yRBEB55c}UgzfV3Jr#7z!U^cWn>T-CNU~+Ub%3r<e_1sTJ+Y;ob(p?&4d9VeR|a!3XpNd2mGKiF#=2f0F>PDv6M5sBj*;}qPSLWv=4vrjz}LJ#s*3%=@@O4E(&%XZWVWGnbpnrNzIIMr;io#F@(O9{{Fex^`m@#Tw&v1J?~&D=N}MYLZu7<=^9>t2he6EWok+uuuNn@0;Zb%r@GuO4=mG`#c&H9DLEn1fF1(y_T~bVfj30TglZ)t&rGORO?*Il>?4n;wvXtuj|kPS-^~#r*kzTv?Z8eRtx5BhEC3NQ0J9<Ut>k#;$gVy7u+^p@lYc*fUZ~at@t%Gjk=VCD=BZgB-PWL5E|~CFZ%FuS-V#e>PpDtu?d|f$ZNfs0wq!wq4Mw>J;hWmwgf4)2LN;m!h`mj0oO2@`UJFxM&tcdA95u2R*;XQ1z;9vB(n`G4Oip-IfF*wZGoYYp+yn$vZob7Iug}@=a9fF$-gkoc`uhabVhmgf0$u{<{<|1=7nY|ou($2Ggc9#>#HPn1epN4KG(2<8d>)w^>j=y#NqqLC@*dj4H~ga$8_R62<L_?zs}@(6_lG6)PA23>H9)?MODiN*v*6EiJgMVg_vPmWmN5eG{Q1Ij4=5DZHE*1Hy9sbY&*7@Oe8E?ky+Q|k?dID8v-EOgiYw3h8P8_pxvV_9+4%3f_kh6Dg&aR&!uq$tI-YK-3nPH&W^ZQwX~+MbRc>|u>Zt_@$?YVNLnN)atv8oOWYhB%MIL>+-q>?T|Jji&qXB3$5|vaYr}=}caQpbnFaHm1if(%',
    'body': 'c-pmC+m0MH5dD{V;bnw;zbtPc#6?0NE-!>A@-;yOhzJP^QU0A%WxKm~XE$s_=$-Ahr)^jHRMn~SygogDmP&h+>dVuW73WiW{OHN)O1ksu@zYn&o;*KYy*_<#x_Y3^S)a{WobCA}x)<Gv=0vrphv(B7?=hF&%d^A)(=9$C8Ce7k_;3wSbAas@AA0rCdL`+d-{xLiH`n|a6QvSoDaTZ->N~DhqY}b*XRQsbQd7}<-_2^eu4mKKOmFx~lBXGCU8!q;5VdU0)b?-d6yXbyn1YiLtlB4}nucn;s{xr1DwfuY<LS1w;9TkjGF78HeV0hYSYJeRS~={$$3v$bJM}m$VsAqP_M=+m<#fxm+14V2PH`$golNSG%AekWCS9~uZ~59F9EjfDoR^&l;ga{6Hbq#ut<W{8_8F;WF3=?POOQL7vB7GzRXMg?4ruzU1Y>Y3nxhj)Vw`Ad=Nv%Z&=fUphC(AwG_B9AkPPXePEB^8`T25yBbq}M)x*0r*M+8cboqB(VQZ3VUtEi~EfnAWp^0B&Vif0aG=inDp|vq6O)T&I^mSlwDcUtCr8Mtql|rUklVTvhA|UOu{RFa3la%g#Yeo!nH+1q?JZ9>+#@50U9oakuev>puL|OuaxuZc03jf>@C5eEyql59)ua0byRvaC;7Rj0&T7o*H^4H5<&1LWhHKV`6UqfqF><%kS)3oexG58n}z~-{K3E9IQ<WlY)jNbK;yWg{?F29wTzouvbHP(sTA&^M@Z|<bkq{Ys8_Bs<ze(YPbEUJ_NYELh2VKS`I@-0MgTa#4#c14xC!BIo~$u{8poo+1LYFh<}t+w93*9EAoFe`d#Sn93;qqyf0yK9zt?hG*4fYkhMA*c=xpkf6-M9t%>H^$Y*vY1~a3GiKRj0BUJt)nxDI;_4lAv4php)i0jdPj^xXgPv`EVh?lKDZ^R?@3L$49#kWooqBA+2JQv4;(jj{^usC_QNH8#=dd&e{Y6~v?O-av$}9<Qd4Q<KgC;L8>L5+>TrHi?Z->hL|&+2EN3u(h{n2%8r!m&+sYf=R!GZw?<r;GN#!<kIZ`c=YGSA+pqeMYGvqtGifK`s!2nEuihbgk04aqvZl>n6Vuq1CikqrC&XSQ!4x?i%#4GU58o-p5@ySz($drwO@RV0|a!VtR$=GsrCW0t3n**Lp&dcsR2BTuz8!IyB;EGSNI#32lh-PAJ)}@S$6|cilqa-krv6SgcVQ7q8Xz1?5MiI+PR>G-l06V9Xop`~KtLky<g0_D5#?gRxW!jXdU@OptJwWv`4O7chrR<IE)!=*G3)ur)LfZhN7oA3N+?Fqh!{(Vs4DUB-9f|*W`*ffC2M6ipR7yiLzK*G9@L~+KN`@1#W3rdc+NX~K!yQmaji?B#k^SI+955)Ex>56+``<~#;~i<UHb-!(wBRfgPP@U`?uHYUA}4dhaL(xnzLr#8QHj-zW2T0$V~nA!AsiwG%s@IlnL33F$G?0k_WE3kBd;B9T=VejT*kQjKS}z}kdB%|ZNf`-P`BjEKN|kaR?GdXu7iB&X;4Dp$()sotcl+jHcjrC>t^i1^f2ZHuourSRq|7}M8com)HRp8{%H8GhZ0bXBVwj7M}kDEj|7B;HDWNHuvBF9v;#WMk`t{_r@e;`DfZiL@lCJIvi5yh_V?Q&nc}Tj_U|-fa7J=nvC5I`CS^`8Lu<aJ3^*dWl);83aXn}zN08`e$1vj!f?p?LV~6j9u#o`<VZSX)ltT^p2Xu0jc6ZE8O+Yx<OdDV|c*dPKTITshYLF<<I5p&Ii2)`fD#z3@Q$p=Ej)KL6x=u0xQ>!pihLJ>yTs&$j8)j<wb8w>FYX;r;I5M~}Nfhi7jKewqjvLBSO@{;y;1?IZSD2|NYTo5JeN*>5c{5WQ0g<wlmp4%wmc%T_mV|>zu3!R6CVoexU=f3wqYi`-*e$@zHO?Y$R(!40b$SWYD1RM(HkktJD7-xvEnK!F=ADXDqa*=zF6$N_ASyx07MheOTo%QNNGw!D3L+#?IAuvViLH{Az-&ooZlmfde3(hYR|9M2hGMTa9Lx<IM$t-@(KsTsX+@kO83V=dvFH$jdkLf9UxjC0Kl0dBZ@6^?ENRsHqiDm{=9z$0`uoCx+x)FYP{!Vl<7F0;p_^+Jr(8c8tr~NQmpEH+&Ns6RkR<M>7Yd4yeFE$g&g91M<x{`7^u=|0_~y+&QacKo',
    'brief_head': 'c-p;JNsrw&4E`@Z`(Q1$q`7r(fo|x67HES&YjWrzK+pn3kpEsTqAbswnKl7Z0S}L~CF&DJex%<luV2MnpU3joa<`jxi7%eNT<(-xmluEh{p#iG<?hY$(Q@~jGHz9NRc77ReO)#jrM0lhu&uQ^wAfN@dskF#2R!K7(V9M5Rjj3!@x3EOHx%#@4hIuyy6Kzo@Sqq`S^+KeDX_q9TkXriYTWkL4nb76<=MJ?EQir}7=?#PWT}?4<L2i+Ak)bzEbTIwX(F2fXOj6fOl$KYb2MPvWi3EUlbokH;oP^VF4yc8LH^`H|7)LXEs>qP*S<O;FaYe0wuzh-$twswxzju1@ACrDss6Ed*LCP|-q$B^ukQOr-rfq9M0c#*z=?<X^b!B}DZ>x27-Xe1x-ZTCAN~Z0arm<ge{NfD<pDqA0fWf!Z^^#Gzj*E&)i&cn$e$r(4UpBnkfAWSii*d;%UexizuSA_zb@+&)VW)oM1uJ_!c@nqwp*CxBAvEw_B#D=k)B@hgoMDpKw#G2i(lmu#6>#PHpfiSmw3u_<D9}iJM|ypSMgo+cU^;ZWs^Yh7{AA<_5I9|$-=-={dVGXnh*2kgYhdAc)W)!<GyThxc9R;WQ6<`Kn8BN7r^iOLqlIngsGde-vsQ35~ob*V-^YKHwbf=coUdhag3xa-M?q8a&amkfEFuG)vaXG5>lOOp^)Z~;&QXBX-GZ%u?Elg1OB?^kZpF+Oe?i+qG36Ur{;-IMKgpIG(60=55`;U+(t2DCOHqe7hsZOpzvoI3ZoYpKvpd>Y#E0P!DB?ml3YaAmE$w^LNH{o%klQz6Zzij)yT1|&U{Y<f8-`5{>WR%=QQOzJfG@ShErVLUDm~mO^ZNl;QbQU@oT*zoVJtK_d@=+{X)<)qZ^d9QpV5qDo?#b9$c^erRD(XiA^Z^bHKl|jF5kjkTLfQLCtRFcyu>|CTEPUg^6`i{Fs)}fu{j?TB~M2aqRAHAX7L?Gexm0rm2q*1+JxV!}H_C=RJTF_B$2(4GO_px!Zxh4nj(2OoPmqZm^SsoAyd71J2K3Ctb&Sk~_RRP<NxGK!Gu_9MVT%tQ>G~N8RM5N(I8>81hd-jVI*Cs2%AGTUKPTPC{C?|G#8}{PQidbO+Lve;Bz+WpdJ&2CQ`8(nFg-{d^E7V?fymw26hEApe4pU09VLUhd{YPk*5Dz-KJ{ae&_xJJG8GdT)xpC@gc}j<mMp;)<7@(LW)gp^VJn`SI??Hwuy>NE)a|Stee1ZgHd9pjKB-N3Ig7xz3EPm53SPp|&s)fq{z4En?E0wP-oAXc>8(I1K4*=zw1(Gt6*+?$t}t|G}MkL|R7+kWqUNZ<rXcO&*_NiE~!kK0gJ?_;$l@2{a=4U~8vY`q&D5hngQ20-kxgMT1TZ5gt6i?|<q|Sv*C6HZ`mo4gmqUwA)c`$MWp$+kXIHY!u4',
    'brief': 'c-pmCNzWa{75y(yirBoMn!DP&2v}s34aq7(s74zBiG>pr2l3xIcc||6Hz1Rk`aX5veqF=4)2Uni)9uac(#F@NzrDSP=6)+LzkYRlVblHg^1FAhU%k1#`04hC+l#;3WbXLYy1Ti@`_1?^sxxS|C%TPfawB0cboIj+H?1*YSb7e4w$q_^H2i+b`@+4^`eycOVz;i2=8eoxy<0Y^YbW%kNzC;8h~Bcu2#kbom-l6->oGocMk4dyzPjH&fm%M?{XM8ob2BrMCOy*oKjJ;KPIuB7ir@T1b2gz_>hLK#z-AsD?A>C9I3xb)l_8TE3^S+6jIU!<&(^6i)&a3Hv|gb@CMge?hD{Ww50mx6?Uc^9=Ll0|mU7HYo>{9A9IJ44LSqGuZBq==I}2{4jRhZ!2x$L<;A7lpiqY&-8r#Y}ZIBMU93BK4#y3q=K_~@wVqLzsqAuYUM;h0f2w@Zv;_Bnaro&o~+z=R7IQ}U(fh-o;x<%oTXA}-cd#ef}5B0-r5{x!(P2!MY4`Y)Pqc}S_$_r8<)68X3WWr6OCGk&q3Xa%C*Xv6vtyWdmi3G<Pkt)_<X(JPn<QWo4dFj77PpvhtZqxZxA~=5{IF7Mg;n<;xM`73dzT}?s(7EDt1jj5}m8R()IC_~N*rTn;gxqNKHex`F<hj0d?U+yq1EXQEW5r4^KO>kPF#Q##+nX4cZ8UO9Wm2HHA>k6q8--Iu>1s4{wz*#(#`U3JyY0&q5wYh+cM^7$oi=tXs>`_yIF;ZK<j)smcVyy51{f_{4i+R%+6M*KHicgsctT}Ek+fv!aLRewL*6fPJ^MIlcFyU}wF0e0AOr)!{9*-weGewLj^3LjRX72dXGLvM7NllBWSA}y?J>jj1ntj@bQdro-CzHwfqz-1zv`rcHu5%RT4FB}&h)G1E{Ph8EFv`R61j_rCZUUppf0;aH}<X~x~yN(WoCl*<x~0Q_C7}6JrD0&2&vPKu}R=r3eAIgxlcRTN4P()XB%=I-Je~1U-T+Q@5-o@U;%4IaM|2eF7*;5D*j3^?Xn=lJXmFB@P5oQ<LZS84miKFNYMWF*tz>WGW!1)vs&8DtPTJnB{!vfX@f$#ZE@>NexY<&P50iixZM)HoBMWbHC`xw_d#}SW=1!+2V8`GWegU}NZwfzE%##4ao}d|&|C2P&if)lpriB|ok7&I06^xT;<?quW={xJ1|x!d3j556Q!n8m6pWaW&T0Bn=<Ahq?)Y!fXCQ3_<y_y?R}ENphH^DW-?>^WArjBF#-<5&S;K33LeO8}ieryw?u|N}f|)0Dyj;JkZb<d#6>qe4!Z8pwis%L`ycxOK)G@s&ly(ZoE5jRrpN;&1ge5g{N5P4Gkg$x)K7T0B$r_}N@qQ;hX7%Z+`XkZ(N;KzzjN8QoS~u;PYX$@XQ`IVHXz3}unJ!i+gYq4-k^daA5t;$vQmw<keE5}?czIenEak|Yt}JslHD^4`Ii5Eswq+*Yz~<E91{+p!N6CWOLelCmp--Tl%_L+@ks|+<V#<#K|MA^%)YsM$MXiK!uM*d_Nxu)j)9T+~^<e0Hpo_PfsK~94|ET-7k{KU@RrVUX2UJYBd#ZhFvvdj|9oRK>R<2s0Lzr2{W$Yq69(6R|{V25fcMq}F_S_$J|DFsRrTD^?yj>~Hu?uD79vLFS8+#5L+0t=UeHt`yfU32)Jp33B1neKD#}8bGXXD56>_4B%WXiXu2MEnU&E&pvl`}ahWh$3J(zmqDNG7)?Y#0hx@Ig6(mVSLrGgc7%s)P*<KL%lA2N1&kwOwKfgy{!4E60n?Locv!M%5mqvXBwaUTB&(kG2MjDu}m++9NT5GNMaN9l9m-*>|Z5Lhf^YQpnT0tfvo4q!`Gwp7v(l8vZ4m7%!hSxQH9Vg~j5SV8J-Vtj}Fg)p{zZIf4KEDE8#QNLlk+?i!nZR^`n~+X#r1S9$x;N_t4{HL)iVU~*cfV;R3AQozwnzb$|;@{qHnky9KhDJ`o;>+2Me)hRz-j#;`OkJ{K1d*`yHFz@s|^7j}ni)X|?ENVf?5lGr@QZ+c4?ZiUOlx%XL?=$p~2tg9NWe^x`$<10sQ*3meoi-6hrl;orJhVgL%u1MLrzxmJwty<1N5b4x$9<jgnjWgR5%`0F!*!z#MEJ4d!OKWm?%lCmcwlxZM5z$t10&(**q}o$ncVSv=pZ`b+Oib!tC+0o3>sH?lh%=%Ps*s_rACA$wazC<|9zA%L(gc23WT_FVSO^mY5}hwO6)q*?!&*gyv2EeON?-SHTn7HUjVxR_&W',
    'footer': 'c-o~_%Z}AJ5dD{I*ks{nY~Ssy&`6BLuwxMNEA&V_TGKEHA^v^NDJSW0n-&_8?%c9v`&8AbDp$TvcelCr*SY;WU2K}C{O0w|bkTO6-n{*CdviBkzD`f3%S#hxGuv6=oou(w)alhc1+0WP$62ef<W_mK;<FSHx*3r%jcFgNF^f>mi7<UkeH(JA{H2l$l)yAIhgr`HOdL4!<is7nVTV?lR_ulVFty$y_Sl|`b`^L<RO)K=YBvD8*?J!7)$RCYxKJGI%U0V$t9E3ne!3e+-Bg_8!#{5P9UGIK)3LEG^tM~YfrI40cB-z6>7IIPYQuoqmlk9Yjy>S0n=w$S=`m2Xh+WS%O5(jfA=dV~ky7O}qzh$8)%=jIX^|?&Az_Y4721%hb!z!Tw7@5QCO(rMy)$n!Y*Tea8xb%Y_r5E)4wlVoPQ%lN<5>C*Y>R*%A$Y#IdZHF7DC?D+S%3^~T)!HaniMy$Jqop0I2bM4K!f;k%6CJ3f1V<_xg2Wm$PpE*VN~pP00!o2wxr5yOMVP}>UB#tUE`6;x-Ia-BfO3j0+8xnKwb1Fb$Qg7u(WK|a+J+44X7^fB^{s*)uwD|Esf06!sk}IORcqMgar<!4Cb`*NIsRpJYq$xN-PDW9m|x?G{&o&cl~U`HshKBd)&E|SQ{3F6W=^muY{|ugsS=iGpnG5D%i_D(^xZ&J9`O@(EZw3<gPeN-MDAupzVmfJg5qFSgAsmTyNQknd`U-+`XBuHG-%TKuWKaKYDri=7En}5nKshd$nrKTIHg6O~FI1Jt7GGH|=6s+(R2Rk`jXl|2*>cM@Jt2=aF|TLLGP$>|D~=j5wkK){JW(5_L?&N)+~RSUAA_^V1=9yx&PWG`RmqhoF3T5OX9r5G1Ck`VsS0OYUggOk+OQGh@zz(1LaQUH=1^rqcyx)24*nq*3fFbVZXb-lm)bNY)pmt&vddAvsGb`3Fi|nEi>^wgA8a#qYUs^}};_*VTv1yRpS+RG85{hzgt9=qxA=zu;QZ)vI{l;6CnYoq*zilHdV)0LnZmcB1o(2BKomJoo7;Sacqx__!FgYtW~C>ly8zD4+MvexwyY7ubbSiV-F@Sd3J1sOlWODlnkyxVWtNnUQ@nx;gexUmBZZkf5R{qcBVzUv{4MATm9XbCLk?h+VNs5~j${7sDG5!7JmdLE52h<1**9A9~zF_tz&T@Q9z`M*>m>-$*7*ufBcz59yyqM*',
}

STYLES = {}


def _load_styles():
    for name, blob in GLYPH_BLOBS.items():
        raw = zlib.decompress(base64.b85decode(blob.encode()))
        data = json.loads(raw.decode())
        glyphs = {}
        for ch, (adv, w, h, dx, dy, hexdata) in data["glyphs"].items():
            glyphs[ch] = (adv, w, h, dx, dy, bytes.fromhex(hexdata))
        STYLES[name] = (data["space_adv"], data["ag_h"], glyphs)


# --------------------------------------------------------------------------
# The day's news — Sunday, 22 November 2026 (frozen data)
# --------------------------------------------------------------------------
LEAD = {
    "kicker": "CLIMATE DIPLOMACY  ·  ANTALYA, TÜRKIYE  ·  TOP STORY",
    "headline": "COP31 Climate Talks Collapse Without a Deal",
    "body": (
        "The UN climate summit ended in disarray: nearly 200 countries failed "
        "to agree on fossil fuels or climate finance despite two days of "
        "overtime talks, leaving the world's climate effort without a roadmap."
    ),
    "chips": ["≈200 nations at the table", "2 days into overtime", "No deal on fossil fuels"],
}

STORIES = [
    {
        "kicker": "RUSSIA–UKRAINE WAR",
        "headline": "Sea Drones Sink Russian Warship off Libya",
        "body": (
            "President Zelenskyy confirmed Ukraine was behind the attack on a "
            "Russian naval vessel docked at Benghazi — a Mediterranean strike, "
            "far from the front line, that widens the war's map."
        ),
    },
    {
        "kicker": "WORLD COURT  ·  THE HAGUE",
        "headline": "ICJ: Myanmar Committed Genocide Against the Rohingya",
        "body": (
            "The International Court of Justice ruled Myanmar's military "
            "committed genocide against the Rohingya. Refugees in Bangladesh "
            "welcomed the verdict — and still want to go home."
        ),
    },
    {
        "kicker": "MIDDLE EAST  ·  THE GULF",
        "headline": "Tankers Struck Near Hormuz; Iran Unveils 'Missile City'",
        "body": (
            "Two tankers were hit near the Strait of Hormuz; Bahrain blamed "
            "Iran for a strike on an industrial site in Sitra. Tehran showed "
            "off a vast underground missile base amid rising US tensions."
        ),
    },
    {
        "kicker": "WEST BANK",
        "headline": "Settler Attacks Torch Homes and Cars Overnight",
        "body": (
            "Israeli settlers raided Palestinian villages near Ramallah, burning "
            "vehicles and homes. Opposition leader Gadi Eisenkot condemned the "
            "attacks as 'terrorism'."
        ),
    },
]

BRIEFS = [
    ("MEXICO", "Cartel boss 'El Chapo Isidro' captured in Sinaloa after a firefight that left 11 dead."),
    ("INDONESIA", "Crews recover more remains in the search for 34 workers missing after a candy-factory fire."),
    ("NIGERIA", "At least 24 people die as a boat carrying mourners to a funeral capsizes."),
    ("TECH", "US officials probe how Nvidia's AI chips reached China despite export controls."),
    ("US POLITICS", "Trump says he'll work with Democrats on a proposed 10% credit-card interest cap."),
]

FOOTER = "Compiled from the day's reports: Open Chronicle · KIRO 7 News · Standard Topic · The Russell Record"

# --------------------------------------------------------------------------
# Canvas drawing
# --------------------------------------------------------------------------
canvas = bytearray(bytes(PAPER) * (W * H))


def rect(x0, y0, x1, y1, color):
    """Filled rectangle, inclusive bounds, clipped to the canvas."""
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W - 1, x1)
    y1 = min(H - 1, y1)
    if x1 < x0 or y1 < y0:
        return
    row = bytes(color) * (x1 - x0 + 1)
    for yy in range(y0, y1 + 1):
        off = (yy * W + x0) * 3
        canvas[off:off + len(row)] = row


def rounded_rect(x0, y0, x1, y1, radius, color):
    """Filled rectangle with rounded corners, inclusive bounds."""
    height = y1 - y0 + 1
    for t in range(height):
        d = min(t, height - 1 - t)
        if d < radius:
            inset = radius - int((radius * radius - (radius - d) ** 2) ** 0.5 + 0.5)
        else:
            inset = 0
        rect(x0 + inset, y0 + t, x1 - inset, y0 + t, color)


def hline(x0, x1, y, color, width=1):
    rect(x0, y, x1, y + width - 1, color)


def vline(x, y0, y1, color, width=1):
    rect(x, y0, x + width - 1, y1, color)


def blit(px, py, w, h, packed, color):
    """Blend one glyph's 4-bit coverage bitmap onto the canvas."""
    fr, fg, fb = color
    idx = 0
    for yy in range(h):
        cy = py + yy
        if cy < 0 or cy >= H:
            idx += w
            continue
        base = cy * W * 3
        for xx in range(w):
            byte = packed[idx >> 1]
            cov = (byte >> 4) if (idx & 1) == 0 else (byte & 15)
            idx += 1
            if cov:
                cx = px + xx
                if 0 <= cx < W:
                    off = base + cx * 3
                    if cov == 15:
                        canvas[off] = fr
                        canvas[off + 1] = fg
                        canvas[off + 2] = fb
                    else:
                        inv = 15 - cov
                        canvas[off] = (fr * cov + canvas[off] * inv) // 15
                        canvas[off + 1] = (fg * cov + canvas[off + 1] * inv) // 15
                        canvas[off + 2] = (fb * cov + canvas[off + 2] * inv) // 15


def measure(text, style):
    """Text width in tenths of a pixel, from the glyph advances."""
    space_adv, _ag_h, glyphs = STYLES[style]
    total = 0
    for ch in text:
        if ch == " ":
            total += space_adv
        else:
            g = glyphs.get(ch)
            total += g[0] if g else space_adv
    return total


def text(x, y, s, style, color):
    """Draw a string with its ascender line at y; returns end x (pixels)."""
    space_adv, _ag_h, glyphs = STYLES[style]
    pen = x * 10
    for ch in s:
        if ch == " ":
            pen += space_adv
            continue
        g = glyphs.get(ch)
        if g is None:
            pen += space_adv
            continue
        adv, w, h, dx, dy, packed = g
        if w:
            blit((pen + 5) // 10 + dx, y + dy, w, h, packed, color)
        pen += adv
    return (pen + 5) // 10


def wrap(s, style, max_width_px):
    """Greedy word wrap; returns lines fitting max_width_px."""
    limit = max_width_px * 10
    lines, current = [], ""
    for word in s.split():
        trial = word if not current else current + " " + word
        if measure(trial, style) <= limit:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_block(x, y, s, style, color, max_width, line_gap=6):
    """Draw wrapped text; returns the y just below the block."""
    _space_adv, ag_h, _glyphs = STYLES[style]
    line_h = ag_h + line_gap
    for line in wrap(s, style, max_width):
        text(x, y, line, style, color)
        y += line_h
    return y


def centered(y, s, style, color):
    w = measure(s, style)
    text((W * 10 - w) // 20, y, s, style, color)
    return y + STYLES[style][1]


# --------------------------------------------------------------------------
# Compose the front page
# --------------------------------------------------------------------------


def build():
    # Outer frame
    rect(14, 14, W - 15, 15, LIGHT_RULE)
    rect(14, H - 16, W - 15, H - 15, LIGHT_RULE)
    rect(14, 14, 15, H - 15, LIGHT_RULE)
    rect(W - 16, 14, W - 15, H - 15, LIGHT_RULE)

    x0, x1 = MARGIN, W - MARGIN
    y = 40

    # Masthead
    y = centered(y, "O N E - P A G E   W O R L D   B R I E F I N G", "top_kicker", ACCENT) + 10
    y = centered(y, "THE WORLD TODAY", "masthead", INK) + 8
    y = centered(y, "Sunday, November 22, 2026  ·  The day's biggest stories, summed up in a single image",
                 "date_line", MUTED) + 14
    hline(x0, x1, y, RULE, 3)
    hline(x0, x1, y + 4, RULE, 1)
    y += 22

    # Lead story
    text(x0, y, LEAD["kicker"], "kicker", ACCENT)
    y += 26
    y = text_block(x0, y, LEAD["headline"], "lead_head", INK, CONTENT_W, line_gap=8) + 6
    y = text_block(x0, y, LEAD["body"], "lead_body", BODY_INK, CONTENT_W, line_gap=9) + 14

    # Lead stat chips
    cx = x0
    for chip in LEAD["chips"]:
        tw = (measure(chip, "chip") + 5) // 10
        rounded_rect(cx, y, cx + tw + 28, y + 34, 8, CHIP_BG)
        text(cx + 14, y + 7, chip, "chip", CHIP_INK)
        cx += tw + 44
    y += 48

    hline(x0, x1, y, LIGHT_RULE, 2)
    y += 20

    # 2 x 2 story grid
    col_gap = 36
    col_w = (CONTENT_W - col_gap) // 2
    grid_top = y
    for row in range(2):
        col_x = [x0, x0 + col_w + col_gap]
        max_bottom = grid_top
        for col in range(2):
            s = STORIES[row * 2 + col]
            sy = grid_top
            text(col_x[col], sy, s["kicker"], "kicker", ACCENT)
            sy += 25
            sy = text_block(col_x[col], sy, s["headline"], "head", INK, col_w, line_gap=5) + 4
            sy = text_block(col_x[col], sy, s["body"], "body", BODY_INK, col_w, line_gap=6)
            max_bottom = max(max_bottom, sy)
        # vertical divider between the two columns
        vline(x0 + col_w + col_gap // 2, grid_top + 2, max_bottom - 4, LIGHT_RULE, 1)
        grid_top = max_bottom + 20
        if row == 0:
            hline(x0, x1, grid_top - 10, LIGHT_RULE, 1)
    y = grid_top + 4

    hline(x0, x1, y, RULE, 2)
    y += 12

    # In brief
    text(x0, y, "AROUND THE WORLD — IN BRIEF", "brief_head", INK)
    y += 32
    for place, line in BRIEFS:
        label = place + "  —  "
        lw = (measure(label, "brief_head") + 5) // 10
        text(x0, y, label, "brief_head", ACCENT)
        y = text_block(x0 + lw, y, line, "brief", BODY_INK, CONTENT_W - lw, line_gap=5) + 5

    # Footer pinned near the foot of the page
    y = max(y + 8, H - 92)
    hline(x0, x1, y, RULE, 1)
    y += 12
    centered(y, FOOTER, "footer", MUTED)


# --------------------------------------------------------------------------
# PNG encoding (zlib, filter 0) and entry point
# --------------------------------------------------------------------------


def encode_png():
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    stride = W * 3
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += canvas[yy * stride:(yy + 1) * stride]
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))


def main():
    _load_styles()
    build()
    out = os.environ.get("ENTRY_OUT")
    if not out:
        base = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
        out = os.path.join(base, "entry.png")
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out, "wb") as f:
        f.write(encode_png())


if __name__ == "__main__":
    main()
