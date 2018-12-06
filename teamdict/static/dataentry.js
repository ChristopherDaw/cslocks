$( document ).ready(() => {
  if (window.File && window.FileReader && window.FileList && window.Blob) {
    disableButtons(true);
  } else {
    alert('Browser does not support File APIs')
  }

  var ALLOWED_TYPES = ['text/plain', 'text/csv'];
  var acceptedFiles = [];
  function handleFileSelect(e) {
    var files = e.target.files; //FileList object
    fileSelectHelper(files);
  }

  function handleFileDrop(e) {
    e.stopPropagation();
    e.preventDefault();
    if (!$('#files')[0].disabled) {
      var files = e.dataTransfer.files;
      fileSelectHelper(files);
    }
  }

  function handleDragOver(e) {
    e.stopPropagation();
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  }

  function fileSelectHelper(files) {
    $('#files')[0].disabled = true;

    var output = [];
    var f;
    for (var i = 0; i < files.length; i++) {
      f = files[i];
      if (ALLOWED_TYPES.includes(f.type)) {
        acceptedFiles.push(f);
        output.push('<li><strong>', escape(f.name), '</strong> (', f.type || 'n/a', ') - ',
                    f.size, ' bytes, last modified: ',
                    f.lastModifiedDate ? f.lastModifiedDate.toLocaleDateString() : 'n/a',
                    '</li>');
      }
    }
    document.getElementById('list').innerHTML = '<ul>' + output.join('') + '</ul>';
    disableButtons(false);
  }

  function readMultipleFiles(files) {
    function readFile(index){
      if (index >= files.length) return "";

      var reader = new FileReader();
      var file = files[index];
      reader.onload = function(e) {
        console.log("data: " + e.target.result);

        $.ajax({
          url: window.location.pathname,
          data: { result: e.target.result },
          method: 'POST'
        })
        .done((res) => {
          getStatus(res.data.task_id, files.length);
        })
        .fail((err) => {
          console.log(err);
        });

        readFile(index + 1);
      }

      reader.readAsText(file);
    }
    readFile(0);
  }

  function handleClick(e) {
    return;
  }

  var dropZone = document.getElementById('dropzone');
  dropZone.addEventListener('dragover', handleDragOver, false);
  dropZone.addEventListener('drop', handleFileDrop, false);
  dropZone.addEventListener('click', handleClick, false);
  document.getElementById('files').addEventListener('change', handleFileSelect, false);

  function disableButtons(status) {
    $(':button').prop('disabled', status);
  }

  /* Ajax asynchronous navigation waiting for server to handle file upload */
  $('button').on('click', function(e) {
    /* TODO:
     * Have readMultipleFiles return or somehow populate a list of taskIDs so we
     * can call getStatus on them and wait while the server populates the table
     */
     e.preventDefault();
     disableButtons(true);

    /* Continue button was pressed, js posts all file data to server asynchronously */
    if ($(this).attr('name') === "continue") {
      readMultipleFiles(acceptedFiles);
    }
    /* Cancel button pressed, server handles cancellation */
    else if ($(this).attr('name') === "cancel") {
      $.ajax({
        url: window.location.pathname,
        data: { navigation: "cancel" },
        method: 'POST'
      })
      .done((res) => {
        getStatus(res.data.task_id, 0);
      })
      .fail((err) => {
        console.log(err);
      });
    }
  });

  var numFinished = 0;
  var numF = 0;
  function getStatus(taskID, numFiles) {
    numF = numFiles;
    $.ajax({
      url: window.location.pathname,
      data: { task_id: taskID },
      method: 'POST'
    })
    .done((res) => {
      const status = res.data.task_status;
      console.log('taskID: ' + taskID + ', status: ' + status);
      if (status === 'finished') {
        numFinished += 1;
        if (numFinished >= acceptedFiles.length) { // >= to account for cancel button press
          console.log('res.data.redirect: ' + res.data.redirect);
          window.location.href = res.data.redirect;
        }
      } else if (status === 'failed') {
          window.location.href = res.data.redirect;
      } else {
        setTimeout(function() {
          getStatus(taskID);
        }, 500);
      }
    })
    .fail((err) => {
      console.log(err);
    });
  }
});
