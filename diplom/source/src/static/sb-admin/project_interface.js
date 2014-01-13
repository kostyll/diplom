// ініціалізація Buble chart масиву
var bubledata = [(['project','m1','m2','project','vulns'])];

var global_item_intex = 0;
// alert(bubledata)

// functions for drawing charts

function drawPieChart(chart_id,array,title) {
  google.load("visualization", "1", {packages:["corechart"]});
  google.setOnLoadCallback(_drawPieChart);
  function _drawPieChart(data,t) {
    var data = google.visualization.arrayToDataTable(array);
    var options = {
      title: title,
      width:  "180px", 
      height: "180px",
    };

    var chart = new google.visualization.PieChart(
      document.getElementById(
        chart_id
        )
      );
    chart.draw(data, options);
  }
}

function drawBubleChart(bubledata, element) {
  // alert(bubledata)
  google.load("visualization", "1", {packages:["corechart"]});
  google.setOnLoadCallback(_drawBubleChart);
  function _drawBubleChart() {
    // alert (bubledata[0]+":"+bubledata[1]);
    var data = google.visualization.arrayToDataTable(bubledata);          
    var options = {
      title: 'Vulns',
      hAxis: {title: 'mackkeib'},
      vAxis: {title: 'holsted'},
      bubble: {textStyle: {fontSize: 11}}
    };

    var chart = new google.visualization.BubbleChart(
              document.getElementById(
                element
                )
              );
    chart.draw(data, options);
  };
  _drawBubleChart(bubledata);
}

function draw3d(data3d, element, widht){
  var data = null;
  var graph = null;

  google.load("visualization", "1");
  
  // Set callback to run when API is loaded
  google.setOnLoadCallback(drawVisualization); 

  function custom(x, y) {
    return (Math.sin(x/50) * Math.cos(y/50) * 50 + 50);
  }

  // Called when the Visualization API is loaded.
  function drawVisualization() {
    // Create and populate a data table.
    data = new google.visualization.DataTable();
    data.addColumn('number', 'x');
    data.addColumn('number', 'y');
    data.addColumn('number', 'z');

    // create some nice looking data with sin/cos
    var steps = 50;  // number of datapoints will be steps*steps
    var axisMax = 314;
    axisStep = axisMax / steps;
    for (var x = 0; x < axisMax; x+=axisStep) {
      for (var y = 0; y < axisMax; y+=axisStep) {
        var value = custom(x,y);
        data.addRow([x, y, value]);
      }
    };

    // specify options
    options = {
               width:  "280px", 
               height: "280px",
               style: "surface",
               showPerspective: true,
               showGrid: true,
               showShadow: false,
               keepAspectRatio: true,
               verticalRatio: 0.5,
               };

    // Instantiate our graph object.
    graph = new links.Graph3d(document.getElementById(element));

    // Draw our graph with the created data and options 
    graph.draw(data, options);
  }
}
function draw3dmodal(data3d, element, widht){
  var data = null;
  var graph = null;

  google.load("visualization", "1");

  // Set callback to run when API is loaded
  google.setOnLoadCallback(drawVisualization); 

  function custom(x, y) {
    // return (Math.sin(x/50) * Math.cos(y/50) * 50 + 50);
    return Math.random()
  }

  // Called when the Visualization API is loaded.
  function drawVisualization() {
    // Create and populate a data table.
    data = new google.visualization.DataTable();
    data.addColumn('number', 'x');
    data.addColumn('number', 'y');
    data.addColumn('number', 'z');

    // create some nice looking data with sin/cos
    var steps = 50;  // number of datapoints will be steps*steps
    var axisMax = 314;
    axisStep = axisMax / steps;
    for (var x = 0; x < axisMax; x+=axisStep) {
      for (var y = 0; y < axisMax; y+=axisStep) {
        var value = custom(x,y);
        data.addRow([x, y, value]);
      }
    };

    // specify options
    options = {
               width:  "500px", 
               height: "480px",
               style: "surface",
               showPerspective: true,
               showGrid: true,
               showShadow: false,
               keepAspectRatio: true,
               verticalRatio: 0.5,
               };

    // Instantiate our graph object.
    graph = new links.Graph3d(document.getElementById(element));

    // Draw our graph with the created data and options 
    graph.draw(data, options);
  }
}

function get_project_sloc_tree(project_name) {
  var result;
  var url = '/ajax/project/'+project_name+'/SLOC/';
  // alert("mrozy");
  //alert (url);
  $.ajax({
      url: url,
      type: "GET",
      dataType : "json",
      async:false,
      success: function(mess){
        result = mess;
        //alert('inside 1 mess',mess);
        //result = mess;  
        //alert('inside 2 mess',mess);
        //alert('inside result',result);
       // return mess.responseJSON;
      }
    });
 // console.log('obj_prop = ', Object.getOwnPropertyNames(x));
  // var response_result = $.getJSON(url);
  // alert('outside',result);

  // var json_string = $.get(url);
  // console.log('json_string=',json_string);
  // console.log(json_string.responseText);

  console.log();
  return result;
}