/***********************************************************************************
****FILENAME:		pu_ssocs20_format.do
****AUTHOR:			United States Department of Education
				    National Center for Education Statistics
****INPUT FILE:		pu_ssocs20.dta

****PURPOSE:
	This file reads in the 2020 School Survey on Crime and Safety (SSOCS:2020)
	Stata dataset and adds value labels.

****A NOTE OF CAUTION:
	The code that follows assumes that the SSOCS:2020 file has been copied
	onto your hard drive into the C:\SSOCS20 directory. If this is not the
	case, you must change C:\SSOCS20 in the library statements below to the path in
	which the pu_ssocs20.dta file is located.

****LAST UPDATED: 1/9/2023
***********************************************************************************/

global ssocslib "C:\SSOCS20"

use "$ssocslib\pu_ssocs20.dta"

label define yesno 1 "Yes" 2 "No"

label define yesno_skip -1 "Legitimate skip" 1 "Yes" 2 "No" 

label define yesnodk_skip -1 "Legitimate skip" 1 "Yes" 2 "No" 3 "Don't know"

label define limit 1 "Limits in major way" 2 "Limits in minor way" 3 "Does not limit"

label define LC0688 1 "None" 2 "1-5" 3 "6-10" 4 "11 or more"

label define happen 1 "Happens daily" 2 "Happens at least once a week" 3 "Happens at least once a month" ///
					4 "Happens on occasion" 5 "Never happens"
					
label define LC0024 -1 "Legitimate skip" 1 "Prekindergarten"
label define LC0026 -1 "Legitimate skip" 1 "Kindergarten"
label define LC0028 -1 "Legitimate skip" 1 "1st"
label define LC0030 -1 "Legitimate skip" 1 "2nd"
label define LC0032 -1 "Legitimate skip" 1 "3rd"
label define LC0034 -1 "Legitimate skip" 1 "4th"
label define LC0036 -1 "Legitimate skip" 1 "5th"
label define LC0038 -1 "Legitimate skip" 1 "6th"
label define LC0040 -1 "Legitimate skip" 1 "7th"
label define LC0042 -1 "Legitimate skip" 1 "8th"
label define LC0044 -1 "Legitimate skip" 1 "9th"
label define LC0046 -1 "Legitimate skip" 1 "10th"
label define LC0048 -1 "Legitimate skip" 1 "11th"
label define LC0050 -1 "Legitimate skip" 1 "12th"
label define LC0052 -1 "Legitimate skip" 1 "Ungraded"

label define LC0560 1 "High level of crime" 2 "Moderate level of crime" 3 "Low level of crime" 4 "Students come from areas with very different levels of crime" 
label define LC0562 1 "High level of crime" 2 "Moderate level of crime" 3 "Low level of crime"

label define month -9 "Missing" 1 "January" 2 "February" 3 "March" 4 "April" 5 "May" 6 "June" 7 "July" 8 "August" 9 "September" 10 "October" 11 "November" 12 "December" 

label define day -9 "Missing"

label define LC0014_R -2 "Missing" 1 "Principal" 2 "Vice principal or disciplinarian" 3 "Security staff" 4 "Other school-level staff" ///
					5 "Superintendent or district staff"

label define LC0076 -2 "Missing" 1 "Yes" 2 "No" 
					 
label define LSTRATA 111 "Primary, <300, City" 112 "Primary, <300, Suburb" 113 "Primary, <300, Town" ///
					114 "Primary, <300, Rural" 121 "Primary, 300-499, City" /// 
					122 "Primary, 300-499, Suburb" 123 "Primary, 300-499, Town" 124 "Primary, 300-499, Rural" /// 
					131 "Primary, 500-999, City" 132 "Primary, 500-999, Suburb" ///
					133	"Primary, 500-999, Town" 134 "Primary, 500-999, Rural" 141 "Primary, 1,000+, City" ///
					142 "Primary, 1,000+, Suburb" 143	"Primary, 1,000+, Town" 144	"Primary, 1000+, Rural" ///
					211	"Middle, <300, City" 212 "Middle, <300, Suburb" 213	"Middle, <300, Town" ///
					214	"Middle, <300, Rural" 221 "Middle, 300-499, City" 222 "Middle, 300-499, Suburb" ///
					223	"Middle, 300-499, Town" 224	"Middle, 300-499, Rural" ///
					231	"Middle, 500-999, City" 232	"Middle, 500-999, Suburb" 233 "Middle, 500-999, Town" ///
					234 "Middle, 500-999, Rural" 241 "Middle, 1,000+, City" ///
					242	"Middle, 1,000+, Suburb" 243 "Middle, 1,000+, Town" 244 "Middle, 1,000+, Rural" ///
					311 "High,  <300, City" 312	"High, <300, Suburb" 313 "High,  <300, Town" ///
					314 "High,  <300, Rural" 321 "High, 300-499, City" 322 "High, 300-499, Suburb" ///
					323 "High, 300-499, Town" 324 "High, 300-499, Rural" 331 "High, 500-999, City" ///
					332 "High, 500-999, Suburb" 333 "High, 500-999, Town" 334 "High, 500-999, Rural" ///
					341	"High, 1,000+, City" 342 "High, 1,000+, Suburb" 343 "High, 1,000+, Town" ///
					344 "High, 1,000+, Rural" 411 "Combined, <300, City" 412 "Combined, <300, Suburb" ///
					414 "Combined, <300, Town or Rural" 422 "Combined, 300-499, City or Suburb" ///
					424 "Combined, 300-499, Town or Rural" 431 "Combined, 500-999, City" ///
					432 "Combined, 500-999, Suburb" 433 "Combined, 500-999, Town" 434 "Combined, 500-999, Rural" ///
					441	"Combined, 1,000+, City" 442 "Combined, 1,000+, Suburb" 443 "Combined, 1,000+, Town" 444 "Combined, 1,000+, Rural"

label define LFR_URBAN 1 "City" 2 "Suburb" 3 "Town" 4 "Rural"
	
label define LFR_LVELX 1 "Elementary" 2 "Middle" 3 "High/Secondary" 4 "Combined/Other"

label define LFR_SIZE 1 "< 300" 2 "300 - 499" 3 "500 - 999" 4 "1,000 +"

label define LPERMINX 1 "Less than 5 percent" 2 "5 percent to less than 20 percent" 3 "20 percent to less than 50 percent" 4 "50 percent or more"

label define LPERCWHTX 1 "More than 95 percent" 2 "More than 80 but less than or equal to 95 percent" ///
						3 "More than 50 but less than or equal to 80 percent" 4 "50 percent or less"
						
label define flag 0 "Not imputed" 7 "Item was imputed by using data from the record for a similar case (donor)" ///
				8 "Item was imputed by using the mean or mode of data for groups of similar cases" ///
				9 "Data value was adjusted during analysts’ post-imputation review of data"

***********CONVERT SELECT VARIABLES TO NUMERIC FORMAT*******
/*
The values of some frame variables on the SSOCS:2020 Public-Use File are in string format.
Because Stata does not allow value labels to be applied to string values, the following
syntax converts these variables to numeric format for the purposes of applying value labels.
*/

destring FR_LVELX PERMINX PERCWHTX, replace
				
				
**********APPLY VALUE LABELS TO VARIABLES*********

label values C0110-C0610 C0266-C0279 C0690_R C0705 C0390 C0394 C0398 C0402 C0406 C0410 C0414 C0418 ///
		C0422 C0426 C0430 C0434 C0438 C0442 C0446 C0450 C0454 yesno

label values C0614-C0650 C0661-C0671 C0392 C0396 C0400 C0404 C0408 C0412 ///
		C0416 C0420 C0424 C0428 C0432 C0436 C0440 C0444 C0448 C0452 C0456 yesno_skip
		
label values C0652-C0660 yesnodk_skip

label values C0674-C0686 C0280-C0296 limit

label values C0374-C0389 happen

label values C0578 month

label values C0579 day

foreach var of varlist C0688 C0024-C0052 C0560-C0014_R C0076 STRATA ///
					   FR_URBAN FR_LVELX FR_SIZE PERMINX PERCWHTX {
			label values `var' L`var'
					   
}

label values IC* flag

