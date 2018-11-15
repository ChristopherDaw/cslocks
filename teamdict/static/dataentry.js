$( document ).ready(() => {
  console.log('sanity check');

  $('button').on('click', function(e) {
    console.log('Button ' + $(this).attr('name') + 'clicked!')
    e.preventDefault();
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
        window.location.href = res.data.redirect;
      }
      setTimeout(function() {
        getStatus(taskID);
      }, 500);
    })
    .fail((err) => {
      console.log(err);
    });
  }
});
