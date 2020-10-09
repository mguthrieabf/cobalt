// send client side errors to the server to log
window.onerror =
function (message, source, lineno, colno, error) {
    console.log(message);
    console.log(source);
    console.log(lineno);
    var errorData = {
      'message': message,
      'url': source,
      'num': lineno,
      'colno': colno,
      'Error object': JSON.stringify(error)
    };
    $.post('/support/browser-errors', {
      data: JSON.stringify(errorData)
    });

  return true;
}

// async function to disable buttons
function disable_submit_button() {
    $(".cobalt-save").each(function() {
      $(this).prop('disabled', true);
  });
};

$(document).ready(function () {

  // block user from double clicking on a submit button.
  // Any button of class cobalt-save will be disabled when
  // a cobalt-save button is clicked

  $(".cobalt-save").click(function () {
      setTimeout(function () { disable_submit_button(); }, 0);
  });

  // prompt for unsaved changes unless button is cobalt-save

  var unsaved = false;

  $(":input").change(function(){
      unsaved = true;
  });

  $('.cobalt-save').click(function() {
      unsaved = false;
  });


  function unloadPage(){
      if(unsaved){
          return "You have unsaved changes on this page. Do you want to leave this page and discard your changes or stay on this page?";
      }
  }

  window.onbeforeunload = unloadPage;


});
