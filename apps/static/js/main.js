function getLog() {
    $.ajax({
     url: '/progress',
     dataType: 'text',
     success: function(text) {
      console.log(text);
      setTimeout(getLog, 1000); //refresh every 1 seconds 
     }
    })
}

getLog(); 