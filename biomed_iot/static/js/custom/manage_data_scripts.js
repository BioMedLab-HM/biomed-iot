$(function(){
    const $meas   = $("#id_measurement");
    const $tags   = $("#id_tags");
    const $toggle = $("#toggle-tags");
  
    const ajaxGetTagsUrl = $("#data-endpoints").data("ajax-get-tags-url");
  
    $toggle.data("allSelected", false);
  
    $meas.on("change", function(){
      $tags.empty();
      $toggle
        .prop("disabled", true)
        .text("Select All Tags")
        .data("allSelected", false);
  
      const meas = $(this).val();
      if (!meas) return;
  
      $.get(ajaxGetTagsUrl, { measurement: meas })
       .done(function(data){
         data.tags.forEach(function(tag){
           $("<option>").val(tag).text(tag).appendTo($tags);
         });
         $toggle.prop("disabled", false);
       });
    });
  
    $toggle.on("click", function(){
      const allSelected = $toggle.data("allSelected");
      if (!allSelected) {
        $tags.find("option").prop("selected", true);
        $toggle
          .text("Reset Tag Selection")
          .data("allSelected", true);
      } else {
        $tags.find("option").prop("selected", false);
        $toggle
          .text("Select All Tags")
          .data("allSelected", false);
      }
      $tags.trigger("change");
    });
  
    $tags.on('mousedown', 'option', function(e) {
      e.preventDefault();
      const $opt = $(this);
      $opt.prop('selected', !$opt.prop('selected'));
      $tags.trigger('change');
    });
  });
  