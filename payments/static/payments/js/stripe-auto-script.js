// A reference to Stripe.js
var stripe;

var orderData = {
  "id": document.getElementById('transID').value,
  "amount": document.getElementById('transAmount').value,
  "description": document.getElementById('transDescription').value
};

// Disable the button until we have Stripe set up on the page
document.querySelector("button").disabled = true;

fetch("create-payment-superintent", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
     "X-CSRFToken": $.cookie("csrftoken")  // This is needed to pass xsite scripting errors
  },
  body: JSON.stringify(orderData)
})
  .then(function(result) {
    return result.json();
  })
  .then(function(data) {
    return setupElements(data);
  })
  .then(function({ stripe, card, clientSecret }) {
    document.querySelector("button").disabled = false;

    // Handle form submission.
    var form = document.getElementById("payment-form");
    form.addEventListener("submit", function(event) {
      event.preventDefault();
      // Initiate payment when the submit button is clicked
      pay(stripe, card, clientSecret);
    });
  });

// Set up Stripe.js and Elements to use in checkout form
var setupElements = function(data) {
  stripe = Stripe(data.publishableKey);
  var elements = stripe.elements();
  var style = {
    base: {
      color: "#32325d",
      fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
      fontSmoothing: "antialiased",
      fontSize: "16px",
      "::placeholder": {
        color: "#aab7c4"
      }
    },
    invalid: {
      color: "#fa755a",
      iconColor: "#fa755a"
    }
  };

  var card = elements.create("card", { hidePostalCode: true, style: style });
  card.mount("#card-element");

  return {
    stripe: stripe,
    card: card,
    clientSecret: data.clientSecret
  };
};

/*
 * Calls stripe.confirmCardPayment which creates a pop-up modal to
 * prompt the user to enter extra authentication details without leaving your page
 */
var pay = function(stripe, card, clientSecret) {
  changeLoadingState(true);

  // Initiate the payment.
  // If authentication is required, confirmCardPayment will automatically display a modal
  stripe
    .confirmCardSetup(clientSecret, {
      payment_method: {
        card: card,
        metadata: {cobalt_tran_type: 'Auto'}
      },
    })
    .then(function(result) {
      if (result.error) {
        // Show error to your customer
        showError(result.error.message);
      } else {
        // The payment has been processed!
        orderComplete(clientSecret);
      }
    });
};

/* ------- Post-payment helpers ------- */

/* Shows a success message when the payment is complete */
var orderComplete = function(clientSecret) {
    $("#cobalt-main-body").html("<h1>Success!</h1><h3>Your card details have been recorded</h3>");
};

var showError = function(errorMsgText) {
  changeLoadingState(false);
  var errorMsg = document.querySelector(".sr-field-error");
  errorMsg.textContent = errorMsgText;
  setTimeout(function() {
    errorMsg.textContent = "";
  }, 4000);
};

// Show a spinner on payment submission
var changeLoadingState = function(isLoading) {
  if (isLoading) {
    document.querySelector("button").disabled = true;
    document.querySelector("#spinner").classList.remove("hidden");
    document.querySelector("#button-text").classList.add("hidden");
  } else {
    document.querySelector("button").disabled = false;
    document.querySelector("#spinner").classList.add("hidden");
    document.querySelector("#button-text").classList.remove("hidden");
  }
};
