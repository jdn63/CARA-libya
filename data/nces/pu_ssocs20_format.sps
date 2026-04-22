* Encoding: UTF-8.

*FILENAME:	    pu_ssocs20_format.sps.

*INPUT FILE:    pu_ssocs20.sav.

*PURPOSE:
	    This file reads in the 2020 School Survey on Crime and Safety (SSOCS:2020)
	    SPSS dataset and adds value labels.

*A NOTE OF CAUTION:
	    The code that follows assumes that the SSOCS:2020 file has been copied
	    onto your hard drive into the C:\SSOCS20 file. If this is not the
	    case, you must change C:\SSOCS20 in the filepath statements below to the path in
	    which the pu_ssocs20.sav file is located.

*LAST UPDATED: 01/06/2022.

GET FILE = 'C:\SSOCS20\pu_ssocs20.sav'.

VALUE LABELS
C0110 to C0610
1 "Yes"
2 "No"/
C0266 to C0279
1 "Yes"
2 "No"/
C0390
1 "Yes"
2 "No"/
C0394
1 "Yes"
2 "No"/
C0398
1 "Yes"
2 "No"/
C0402
1 "Yes"
2 "No"/
C0406
1 "Yes"
2 "No"/
C0410
1 "Yes"
2 "No"/
C0414
1 "Yes"
2 "No"/
C0418
1 "Yes"
2 "No"/
C0422
1 "Yes"
2 "No"/
C0426
1 "Yes"
2 "No"/
C0430
1 "Yes"
2 "No"/
C0434
1 "Yes"
2 "No"/
C0438
1 "Yes"
2 "No"/
C0442
1 "Yes"
2 "No"/
C0446
1 "Yes"
2 "No"/
C0450
1 "Yes"
2 "No"/
C0454
1 "Yes"
2 "No".

VALUE LABELS
C0614 to C0650
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0661 to C0671
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0392
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0396
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0400
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0404
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0408
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0412
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0416
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0420
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0424
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0428
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0432
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0436
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0440
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0444
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0448
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0452
-1 "Legitimate skip"
1 "Yes"
2 "No"/
C0456
-1 "Legitimate skip"
1 "Yes"
2 "No".

VALUE LABELS
C0652 to C0660
-1 "Legitimate skip"
1 "Yes"
2 "No"
3 "Don't Know".

VALUE LABELS
C0674 to C0686
1 "Limits in major way"
2 "Limits in minor way"
3 "Does not limit"/
C0280 to C0296
1 "Limits in major way"
2 "Limits in minor way"
3 "Does not limit".

VALUE LABELS
C0374 to C0389
1 "Happens daily"
2 "Happens at least once a week"
3 "Happens at least once a month"
4 "Happens on occasion"
5 "Never Happens".

VALUE LABELS
C0579
-9 "Missing".

VALUE LABELS
C0024
-1 "Legitimate skip"
1 "Prekindergarten"/
C0026
-1 "Legitimate skip"
1 "Kindergarten"/
C0028
-1 "Legitimate skip"
1 "1st"/
C0030
-1 "Legitimate skip"
1 "2nd"/
C0032
-1 "Legitimate skip"
1 "3rd"/
C0034
-1 "Legitimate skip"
1 "4th"/
C0036
-1 "Legitimate skip"
1 "5th"/
C0038
-1 "Legitimate skip"
1 "6th"/
C0040
-1 "Legitimate skip"
1 "7th"/
C0042
-1 "Legitimate skip"
1 "8th"/
C0044
-1 "Legitimate skip"
1 "9th"/
C0046
-1 "Legitimate skip"
1 "10th"/
C0048
-1 "Legitimate skip"
1 "11th"/
C0050
-1 "Legitimate skip"
1 "12th"/
C0052
-1 "Legitimate skip"
1 "Ungraded".

VALUE LABELS
C0560 to C0562
1 "High level of crime"
2 "Moderate level of crime"
3 "Low level of crime"
4 "Students come from areas with very different levels of crime".

VALUE LABELS
C0076
-2 "Missing"
1 "Yes"
2 "No".

VALUE LABELS
C0014_R
-2 "Missing"
1 "Principal"
2 "Vice principal or disciplinarian"
3 "Security staff"
4 "Other school-level staff"
5 "Superintendent or district staff".

VALUE LABELS
C0690_R
1 "Yes"
2 "No".

VALUE LABELS
STRATA
111 "Primary, <300, City"
112 "Primary, <300, Suburb"
113 "Primary, <300, Town"
114 "Primary, <300, Rural"
121 "Primary, 300-499, City"
122 "Primary, 300-499, Suburb"
123 "Primary, 300-499, Town"
124 "Primary, 300-499, Rural"
131 "Primary, 500-999, City"
132 "Primary, 500-999, Suburb"
133 "Primary, 500-999, Town"
134 "Primary, 500-999, Rural"
141 "Primary, 1,000+, City"
142 "Primary, 1,000+, Suburb"
143 "Primary, 1,000+, Town"
144 "Primary, 1000+, Rural"
211 "Middle, <300, City"
212 "Middle, <300, Suburb"
213 "Middle, <300, Town"
214 "Middle, <300, Rural"
221 "Middle, 300-499, City"
222 "Middle, 300-499, Suburb"
223 "Middle, 300-499, Town"
224 "Middle, 300-499, Rural"
231 "Middle, 500-999, City"
232 "Middle, 500-999, Suburb"
233 "Middle, 500-999, Town"
234 "Middle, 500-999, Rural"
241 "Middle, 1,000+, City"
242 "Middle, 1,000+, Suburb"
243 "Middle, 1,000+, Town"
244 "Middle, 1,000+, Rural"
311 "High, <300, City"
312 "High, <300, Suburb"
313 "High, <300, Town"
314 "High, <300, Rural"
321 "High, 300-499, City"
322 "High, 300-499, Suburb"
323 "High, 300-499, Town"
324 "High, 300-499, Rural"
331 "High, 500-999, City"
332 "High, 500-999, Suburb"
333 "High, 500-999, Town"
334 "High, 500-999, Rural"
341 "High, 1,000+, City"
342 "High, 1,000+, Suburb"
343 "High, 1,000+, Town"
344 "High, 1,000+, Rural"
411 "Combined, <300, City"
412 "Combined, <300, Suburb"
414 "Combined, <300, Town or Rural"
422 "Combined, 300-499, City or Suburb"
424 "Combined, 300-499, Town or Rural"
431 "Combined, 500-999, City"
432 "Combined, 500-999, Suburb"
433 "Combined, 500-999, Town"
434 "Combined, 500-999, Rural"
441 "Combined, 1,000+, City"
442 "Combined, 1,000+, Suburb"
443 "Combined, 1,000+, Town"
444 "Combined, 1,000+, Rural".

VALUE LABELS
FR_URBAN
1 "City"
2 "Suburb"
3 "Town"
4 "Rural".

VALUE LABELS
FR_LVELX
1 "Elementary"
2 "Middle"
3 "High/Secondary"
4 "Combined/Other".

VALUE LABELS
FR_SIZE
1 "< 300"
2 "300 - 499"
3 "500 - 999"
4 "1,000 +".

VALUE LABELS
PERMINX
1 "Less than 5 percent"
2 "5 percent to less than 20 percent"
3 "20 percent to less than 50 percent"
4 "50 percent or more".

VALUE LABELS
PERCWHTX
1 "More than 95 percent"
2 "More than 80 but less than or equal to 95 percent"
3 "More than 50 but less than or equal to 80 percent"
4 "50 percent or less".

VALUE LABELS
IC0110 to IC0580
0 "Not imputed"
7 "Item was imputed by using data from the record for a similar case (donor)"
8 "Item was imputed by using the mean or mode of data for groups of similar cases"
9 "Data value was adjusted during analysts’ post-imputation review of data".

EXECUTE.
