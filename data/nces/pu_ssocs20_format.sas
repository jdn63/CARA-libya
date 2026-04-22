***********************************************************************************
****FILENAME:		pu_ssocs20_format.sas
****AUTHOR:			United States Department of Education
				    National Center for Education Statistics
****INPUT FILE:		pu_ssocs20.sas7dbat

****PURPOSE:
	This file reads in the 2020 School Survey on Crime and Safety (SSOCS:2020)
	unformatted SAS dataset and adds value labels.

****A NOTE OF CAUTION:
	The code that follows assumes that the SSOCS:2020 file has been copied
	onto your hard drive into the C:\SSOCS20 directory. If this is not the
	case, you must change C:\SSOCS20 in the libname statements below to the path in
	which the pu_ssocs20.sas7bdat file is located.

****LAST UPDATED: 1/11/2023
***********************************************************************************;

libname SSOCS "C:\SSOCS20"; *see NOTE above;

proc format;
value	C0110F
1	="Yes"
2	="No"
;	
	
value	C0112F
1	="Yes"
2	="No"
;	
	
value	C0114F
1	="Yes"
2	="No"
;	
	
value	C0116F
1	="Yes"
2	="No"
;	
	
value	C0120F
1	="Yes"
2	="No"
;	
	
value	C0121F
1	="Yes"
2	="No"
;	
	
value	C0122F
1	="Yes"
2	="No"
;	
	
value	C0125F
1	="Yes"
2	="No"
;	
	
value	C0129F
1	="Yes"
2	="No"
;	
	
value	C0134F
1	="Yes"
2	="No"
;	
	
value	C0136F
1	="Yes"
2	="No"
;	
	
value	C0138F
1	="Yes"
2	="No"
;	
	
value	C0140F
1	="Yes"
2	="No"
;	
	
value	C0139F
1	="Yes"
2	="No"
;	
	
value	C0141F
1	="Yes"
2	="No"
;	
	
value	C0143F
1	="Yes"
2	="No"
;	
	
value	C0142F
1	="Yes"
2	="No"
;	
	
value	C0144F
1	="Yes"
2	="No"
;	
	
value	C0146F
1	="Yes"
2	="No"
;	
	
value	C0150F
1	="Yes"
2	="No"
;	
	
value	C0153F
1	="Yes"
2	="No"
;	
	
value	C0155F
1	="Yes"
2	="No"
;	
	
value	C0158F
1	="Yes"
2	="No"
;	
	
value	C0162F
1	="Yes"
2	="No"
;	
	
value	C0166F
1	="Yes"
2	="No"
;	
	
value	C0170F
1	="Yes"
2	="No"
;	
	
value	C0169F
1	="Yes"
2	="No"
;	
	
value	C0161F
1	="Yes"
2	="No"
;	
	
value	C0157F
1	="Yes"
2	="No"
;	
	
value	C0163F
1	="Yes"
2	="No"
;	
	
value	C0165F
1	="Yes"
2	="No"
;	
	
value	C0167F
1	="Yes"
2	="No"
;	
	
value	C0174F
1	="Yes"
2	="No"
;	
	
value	C0183F
1	="Yes"
2	="No"
;	
	
value	C0176F
1	="Yes"
2	="No"
;	
	
value	C0181F
1	="Yes"
2	="No"
;	
	
value	C0175F
1	="Yes"
2	="No"
;	
	
value	C0177F
1	="Yes"
2	="No"
;	
	
value	C0179F
1	="Yes"
2	="No"
;	
	
value	C0186F
1	="Yes"
2	="No"
;	
	
value	C0600F
1	="Yes"
2	="No"
;	

value	C0604F
1	="Yes"
2	="No"
;	
	
value	C0606F
1	="Yes"
2	="No"
;	
	
value	C0608F
1	="Yes"
2	="No"
;	
	
value	C0190F
1	="Yes"
2	="No"
;	
	
value	C0192F
1	="Yes"
2	="No"
;	
		
value	C0204F
1	="Yes"
2	="No"
;	
	
value	C0206F
1	="Yes"
2	="No"
;	
	
value	C0208F
1	="Yes"
2	="No"
;	
	
value	C0210F
1	="Yes"
2	="No"
;	
	
value	C0212F
1	="Yes"
2	="No"
;	
	
value	C0214F
1	="Yes"
2	="No"
;	
	
value	C0216F
1	="Yes"
2	="No"
;	
	
value	C0218F
1	="Yes"
2	="No"
;	
	
value	C0610F
1	="Yes"
2	="No"
;	
	
value	C0614F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0616F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0618F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0621F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0622F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0624F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0626F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0628F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0630F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0632F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0636F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0638F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0640F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0642F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0644F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0646F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	

value	C0650F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0652F
-1	="Legitimate skip"
1	="Yes"
2	="No"
3	="Don't Know"
;	
	
value	C0654F
-1	="Legitimate skip"
1	="Yes"
2	="No"
3	="Don't Know"
;	
	
value	C0656F
-1	="Legitimate skip"
1	="Yes"
2	="No"
3	="Don't Know"
;	
	
value	C0658F
-1	="Legitimate skip"
1	="Yes"
2	="No"
3	="Don't Know"
;	
	
value	C0660F
-1	="Legitimate skip"
1	="Yes"
2	="No"
3	="Don't Know"
;	
	
value	C0661F
1	="Yes"
2	="No"
;	
	
value	C0663F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0665F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0667F
1	="Yes"
2	="No"
;	
	
value	C0669F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0671F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0674F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0676F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0678F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0681F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0682F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0684F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0686F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0266F
1	="Yes"
2	="No"
;	
	
value	C0268F
1	="Yes"
2	="No"
;	
	
value	C0265F
1	="Yes"
2	="No"
;	
	
value	C0267F
1	="Yes"
2	="No"
;	
	
value	C0269F
1	="Yes"
2	="No"
;	
	
value	C0270F
1	="Yes"
2	="No"
;	
	
value	C0272F
1	="Yes"
2	="No"
;	
	
value	C0278F
1	="Yes"
2	="No"
;	
	
value	C0271F
1	="Yes"
2	="No"
;	
	
value	C0273F
1	="Yes"
2	="No"
;	
	
value	C0274F
1	="Yes"
2	="No"
;	
	
value	C0276F
1	="Yes"
2	="No"
;	
	
value	C0277F
1	="Yes"
2	="No"
;	
	
value	C0279F
1	="Yes"
2	="No"
;	
	
value	C0280F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0282F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0284F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0286F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0288F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0290F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0292F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0294F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
value	C0296F
1	="Limits in major way"
2	="Limits in minor way"
3	="Does not limit"
;	
	
	
value	C0705F
1	="Yes"
2	="No"
;	
	
value	C0688F
1	="None"
2	="1-5"
3	="6-10"
4	="11 or more"
;	
	
value	C0374F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0376F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0378F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0381F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0383F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0385F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0387F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0382F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0380F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0384F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0386F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0389F
1	="Happens daily"
2	="Happens at least once a week"
3	="Happens at least once a month"
4	="Happens on occasion"
5	="Never happens"
;	
	
value	C0390F
1	="Yes"
2	="No"
;	
	
value	C0392F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0394F
1	="Yes"
2	="No"
;	
	
value	C0396F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0398F
1	="Yes"
2	="No"
;	
	
value	C0400F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0402F
1	="Yes"
2	="No"
;	
	
value	C0404F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0406F
1	="Yes"
2	="No"
;	
	
value	C0408F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0410F
1	="Yes"
2	="No"
;	
	
value	C0412F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0414F
1	="Yes"
2	="No"
;	
	
value	C0416F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0418F
1	="Yes"
2	="No"
;	
	
value	C0420F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0422F
1	="Yes"
2	="No"
;	
	
value	C0424F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0426F
1	="Yes"
2	="No"
;	
	
value	C0428F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0430F
1	="Yes"
2	="No"
;	
	
value	C0432F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0434F
1	="Yes"
2	="No"
;	
	
value	C0436F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0438F
1	="Yes"
2	="No"
;	
	
value	C0440F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0442F
1	="Yes"
2	="No"
;	
	
value	C0444F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0446F
1	="Yes"
2	="No"
;	
	
value	C0448F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0450F
1	="Yes"
2	="No"
;	
	
value	C0452F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0454F
1	="Yes"
2	="No"
;	
	
value	C0456F
-1	="Legitimate skip"
1	="Yes"
2	="No"
;	
	
value	C0560F
1	="High level of crime"
2	="Moderate level of crime"
3	="Low level of crime"
4	="Students come from areas with very different levels of crime"
;	
	
value	C0562F
1	="High level of crime"
2	="Moderate level of crime"
3	="Low level of crime"
;	

value	C0024F
-1	="Legitimate skip"
1	="Prekindergarten"
;

value	C0026F
-1	="Legitimate skip"
1	="Kindergarten"
;

value	C0028F
-1	="Legitimate skip"
1	="1st"
;

value	C0030F
-1	="Legitimate skip"
1	="2nd"
;

value	C0032F
-1	="Legitimate skip"
1	="3rd"
;

value	C0034F
-1	="Legitimate skip"
1	="4th"
;

value	C0036F
-1	="Legitimate skip"
1	="5th"
;

value	C0038F
-1	="Legitimate skip"
1	="6th"
;

value	C0040F
-1	="Legitimate skip"
1	="7th"
;

value	C0042F
-1	="Legitimate skip"
1	="8th"
;

value	C0044F
-1	="Legitimate skip"
1	="9th"
;

value	C0046F
-1	="Legitimate skip"
1	="10th"
;

value	C0048F
-1	="Legitimate skip"
1	="11th"
;

value	C0050F
-1	="Legitimate skip"
1	="12th"
;

value	C0052F
-1	="Legitimate skip"
1	="Ungraded"
;

value	C0076F
-2	="Missing"
1	="Yes"
2	="No"
;

value	C0578F
-9	="Missing" 
1	="January" 
2	="February" 
3	="March" 
4	="April" 
5	="May" 
6	="June" 
7	="July" 
8	="August" 
9	="September" 
10	="October" 
11	="November" 
12	="December"
;

value C0579F
-9	="Missing" 
;

value C0014_RF
-2	="Missing"
1	="Principal"
2	="Vice principal or disciplinarian"
3	="Security staff"
4	="Other school-level staff"
5	="Superintendent or district staff"
;

value C0690_RF
1	="Yes"
2	="No"
;

value	STRATAF
111	="Primary, <300, City"
112	="Primary, <300, Suburb"
113	="Primary, <300, Town"
114	="Primary, <300, Rural"
121	="Primary, 300-499, City"
122	="Primary, 300-499, Suburb"
123	="Primary, 300-499, Town"
124	="Primary, 300-499, Rural"
131	="Primary, 500-999, City"
132	="Primary, 500-999, Suburb"
133	="Primary, 500-999, Town"
134	="Primary, 500-999, Rural"
141	="Primary, 1,000+, City"
142	="Primary, 1,000+, Suburb"
143	="Primary, 1,000+, Town"
144	="Primary, 1000+, Rural"
211	="Middle, <300, City"
212	="Middle, <300, Suburb"
213	="Middle, <300, Town"
214	="Middle, <300, Rural"
221	="Middle, 300-499, City"
222	="Middle, 300-499, Suburb"
223	="Middle, 300-499, Town"
224	="Middle, 300-499, Rural"
231	="Middle, 500-999, City"
232	="Middle, 500-999, Suburb"
233	="Middle, 500-999, Town"
234	="Middle, 500-999, Rural"
241	="Middle, 1,000+, City"
242	="Middle, 1,000+, Suburb"
243	="Middle, 1,000+, Town"
244	="Middle, 1,000+, Rural"
311	="High,  <300, City"
312	="High, <300, Suburb"
313	="High,  <300, Town"
314	="High,  <300, Rural"
321	="High, 300-499, City"
322	="High, 300-499, Suburb"
323	="High, 300-499, Town"
324	="High, 300-499, Rural"
331	="High, 500-999, City"
332	="High, 500-999, Suburb"
333	="High, 500-999, Town"
334	="High, 500-999, Rural"
341	="High, 1,000+, City"
342	="High, 1,000+, Suburb"
343	="High, 1,000+, Town"
344	="High, 1,000+, Rural"
411	="Combined, <300, City"
412	="Combined, <300, Suburb"
414	="Combined, <300, Town or Rural"
422	="Combined, 300-499, City or Suburb"
424	="Combined, 300-499, Town or Rural"
431	="Combined, 500-999, City"
432	="Combined, 500-999, Suburb"
433	="Combined, 500-999, Town"
434	="Combined, 500-999, Rural"
441	="Combined, 1,000+, City"
442	="Combined, 1,000+, Suburb"
443	="Combined, 1,000+, Town"
444	="Combined, 1,000+, Rural"
;	
	
value	FR_URBANF
1	="City"
2	="Suburb"
3	="Town"
4	="Rural"
;

value	$FR_LVELXF
"1" ="Elementary"
"2" ="Middle"
"3" ="High/Secondary"
"4" ="Combined/Other"
;	
	
value	FR_SIZEF
1	="< 300"
2	="300 - 499"
3	="500 - 999"
4	="1,000 +"
;	
	
value	$PERMINXF
"1" ="Less than 5 percent"
"2" ="5 percent to less than 20 percent"
"3" ="20 percent to less than 50 percent"
"4" ="50 percent or more"
;	
	
value	$PERCWHTXF
"1" ="More than 95 percent"
"2" ="More than 80 but less than or equal to 95 percent"
"3" ="More than 50 but less than or equal to 80 percent"
"4" ="50 percent or less"
;	
	
	
value     IMPF
0         ="Not imputed"
7         ="Item was imputed by using data from the record for a similar case (donor)"
8         ="Item was imputed by using the mean or mode of data for groups of similar cases"
9         ="Data value was adjusted during analysts’ post-imputation review of data"
;

data SSOCS.pu_ssocs20_fmt; 
set SSOCS.pu_ssocs20;
format
C0110			C0110F.	
C0112			C0112F.	
C0114			C0114F.	
C0116			C0116F.	
C0120			C0120F.	
C0121			C0121F.	
C0122			C0122F.	
C0125			C0125F.	
C0129			C0129F.	
C0134			C0134F.	
C0136			C0136F.	
C0138			C0138F.	
C0140			C0140F.	
C0139			C0139F.	
C0141			C0141F.	
C0143			C0143F.	
C0142			C0142F.	
C0144			C0144F.	
C0146			C0146F.	
C0150			C0150F.	
C0153			C0153F.	
C0155			C0155F.	
C0158			C0158F.	
C0162			C0162F.	
C0166			C0166F.	
C0170			C0170F.	
C0169			C0169F.	
C0161			C0161F.	
C0157			C0157F.	
C0163			C0163F.	
C0165			C0165F.	
C0167			C0167F.	
C0174			C0174F.	
C0183			C0183F.	
C0176			C0176F.	
C0181			C0181F.	
C0175			C0175F.	
C0177			C0177F.	
C0179			C0179F.	
C0186			C0186F.	
C0600			C0600F.	
C0604			C0604F.	
C0606			C0606F.	
C0608			C0608F.	
C0190			C0190F.	
C0192			C0192F.	
C0204			C0204F.	
C0206			C0206F.	
C0208			C0208F.	
C0210			C0210F.	
C0212			C0212F.	
C0214			C0214F.	
C0216			C0216F.	
C0218			C0218F.	
C0610			C0610F.	
C0614			C0614F.	
C0616			C0616F.	
C0618			C0618F.	
C0621			C0621F.	
C0622			C0622F.	
C0624			C0624F.	
C0626			C0626F.	
C0628			C0628F.	
C0630			C0630F.	
C0632			C0632F.	
C0636			C0636F.	
C0638			C0638F.	
C0640			C0640F.	
C0642			C0642F.	
C0644			C0644F.	
C0646			C0646F.	
C0650			C0650F.	
C0652			C0652F.	
C0654			C0654F.	
C0656			C0656F.	
C0658			C0658F.	
C0660			C0660F.	
C0661			C0661F.	
C0663			C0663F.	
C0665			C0665F.	
C0667			C0667F.	
C0669			C0669F.	
C0671			C0671F.	
C0674			C0674F.	
C0676			C0676F.	
C0678			C0678F.	
C0681			C0681F.	
C0682			C0682F.	
C0684			C0684F.	
C0686			C0686F.	
C0266			C0266F.	
C0268			C0268F.	
C0265			C0265F.	
C0267			C0267F.	
C0269			C0269F.	
C0270			C0270F.	
C0272			C0272F.	
C0278			C0278F.	
C0271			C0271F.	
C0273			C0273F.	
C0274			C0274F.	
C0276			C0276F.	
C0277			C0277F.	
C0279			C0279F.	
C0280			C0280F.	
C0282			C0282F.	
C0284			C0284F.	
C0286			C0286F.	
C0288			C0288F.	
C0290			C0290F.	
C0292			C0292F.	
C0294			C0294F.	
C0296			C0296F.	
C0705			C0705F.	
C0688			C0688F.	
C0374			C0374F.	
C0376			C0376F.	
C0378			C0378F.	
C0381			C0381F.	
C0383			C0383F.	
C0385			C0385F.	
C0387			C0387F.	
C0382			C0382F.	
C0380			C0380F.	
C0384			C0384F.	
C0386			C0386F.	
C0389			C0389F.	
C0390			C0390F.	
C0392			C0392F.	
C0394			C0394F.	
C0396			C0396F.	
C0398			C0398F.	
C0400			C0400F.	
C0402			C0402F.	
C0404			C0404F.	
C0406			C0406F.	
C0408			C0408F.	
C0410			C0410F.	
C0412			C0412F.	
C0414			C0414F.	
C0416			C0416F.	
C0418			C0418F.	
C0420			C0420F.	
C0422			C0422F.	
C0424			C0424F.	
C0426			C0426F.	
C0428			C0428F.	
C0430			C0430F.	
C0432			C0432F.	
C0434			C0434F.	
C0436			C0436F.	
C0438			C0438F.	
C0440			C0440F.	
C0442			C0442F.	
C0444			C0444F.	
C0446			C0446F.	
C0448			C0448F.	
C0450			C0450F.	
C0452			C0452F.	
C0454			C0454F.	
C0456			C0456F.	
C0560			C0560F.	
C0562			C0562F.	
C0024			C0024F.
C0026			C0026F.
C0028			C0028F.
C0030			C0030F.
C0032			C0032F.
C0034			C0034F.
C0036			C0036F.
C0038			C0038F.
C0040			C0040F.
C0042			C0042F.
C0044			C0044F.
C0046			C0046F.
C0048			C0048F.
C0050			C0050F.
C0052			C0052F.	
C0076			C0076F.
C0578			C0578F.
C0579			C0579F.
C0014_R			C0014_RF.
C0690_R			C0690_RF.				
STRATA			STRATAF.		
FR_URBAN		FR_URBANF.
FR_LVELX	     $FR_LVELXF.	
FR_SIZE			FR_SIZEF.	
PERMINX		     $PERMINXF.	
PERCWHTX		$PERCWHTXF.				
IC:			IMPF.
;
run;
