SELECT ABFNumber, mps, postingmonth, postingyear, MPColour, EventDescription, EventCode FROM dbo.viewPlayerTrans  where ABFNumber > 900000 and ABFNumber < 999990;
