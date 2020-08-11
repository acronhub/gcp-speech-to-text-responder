function getLog() {
    $.ajax({
     url: '/progress',
     dataType: 'text',
     success: function(json) {
        const obj = JSON.parse(json);
        const time = parseInt(obj.time);
        if (time != -1) {
            // プログレスバー表示
            document.getElementById("progress-convert").style.display = "flex";
            document.getElementById("form-convert").style.display = "none";

            document.getElementById("progress-bar-convert").style.width = time + '%';
            document.getElementById("progress-bar-convert").innerHTML = time + '%';
        } else {
            // フォーム 表示
            document.getElementById("progress-convert").style.display = "none";
            document.getElementById("form-convert").style.display = "block";
        }

        setTimeout(getLog, 1000); //refresh every 1 seconds 
     }
    })
}

getLog(); 