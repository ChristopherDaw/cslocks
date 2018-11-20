$( document ).ready(() => {
  if (window.File && window.FileReader && window.FileList && window.Blob) {
    disableButtons(true);
  } else {
    alert('Browser does not support File APIs')
  }

  var ALLOWED_TYPES = ['text/plain', 'text/csv'];
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
    for (var i = 0, f; f = files[i]; i++) {
      if (ALLOWED_TYPES.includes(f.type)) {
        output.push('<li><strong>', escape(f.name), '</strong> (', f.type || 'n/a', ') - ',
                    f.size, ' bytes, last modified: ',
                    f.lastModifiedDate ? f.lastModifiedDate.toLocaleDateString() : 'n/a',
                    '</li>');

        var reader = new FileReader();
        reader.onload = function(e) {
          console.log(reader.result);
          $.ajax({
            url: window.location.pathname,
            data: { result: reader.result },
            method: 'POST'
          })
          .done((res) => {
            getStatus(res.data.task_id);
          })
          .fail((err) => {
            console.log(err);
          });
        }

        reader.readAsText(f);


      }
    }
    document.getElementById('list').innerHTML = '<ul>' + output.join('') + '</ul>';
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
    e.preventDefault();
    disableButtons(true);
    $.ajax({
      url: window.location.pathname,
      data: { navigation: $(this).attr('name') },
      method: 'POST'
    })
    .done((res) => {
      getStatus(res.data.task_id);
    })
    .fail((err) => {
      console.log(err);
    });
  });

  function getStatus(taskID) {
    $.ajax({
      url: window.location.pathname,
      data: { task_id: taskID },
      method: 'POST'
    })
    .done((res) => {
      const status = res.data.task_status;
      console.log('taskID: ' + taskID + ', status: ' + status)
      if (status === 'finished' || status === 'failed') {
        disableButtons(false);
        //window.location.href = res.data.redirect;
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
