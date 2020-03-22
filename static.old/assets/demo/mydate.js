


function nth(d) {
  if (d > 3 && d < 21) return 'th';
  switch (d % 10) {
    case 1:  return "st";
    case 2:  return "nd";
    case 3:  return "rd";
    default: return "th";
  }
}

function showDate(n) {

  if (n==0) {
    return("Today");
  } else if (n==-1) {
    return("Yesterday");
  } else if (n==1) {
    return("Tomorrow");

  } else {

    month_names_short=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    date = new Date();
    date.setDate(date.getDate() + n);
    y = date.getFullYear();
    m = month_names_short[date.getMonth()];
    d = date.getDate();
    th=nth(d);
    return(d + th+ " " + m + " " + y);
  }
}
