var SUB = {
  staticBucket: "",
  mediaBucket: "",
  dynamo: "",
  steps:[
    "ORIGINAL",
    "TRANSCODED",
    "TRANSCRIBING",
    "TRANSLATED",
    "DONE"
  ]
};

// Upload a file in multi part to the mediaBucket
var upload = function(callback){
  var file = $('#file')[0].files[0];
  if ( !file ){
    $("#uploadError").removeClass("d-none");
    callback(true);
  }
  var fileName = file.name.replace(".mp4", '')
    .replace(/[^\w\s]/gi, '')
    .replace(/ /gi, "-") + ".mp4";
  var params = {Key: "0-input/" + fileName, ContentType: file.type, Body: file};
  var options = {partSize: 5242880, queueSize: 1};
  console.log("Sending the file by 5M packets", params);
  SUB.mediaBucket.upload( params, options ).promise().then(function(data){
    console.log('Upload over');
    return callback();
  }).catch(function(err) {
    console.log(err);
  });
}

// Show a specific video
var showVideo = function(e){
  var id = e.currentTarget.id;

  $("#video").empty();
  var video = document.createElement("video");
  video.setAttribute("controls", "")
  video.setAttribute("height", "480");
  video.setAttribute("width", "640");

  var source = document.createElement("source");
  source.setAttribute("src", "/files/"+id+"/"+id+".mp4");
  source.setAttribute("type", "video/mp4");
  video.append(source);

  var languages = {
    "ar": "العربية",
    "de": "Deutsch",
    "es": "Español",
    "en": "English",
    "fr": "Français",
    // "pt": "Português",
    "zh": "中国"
  };

  $.each(languages, function(index, language){
    var track = document.createElement("track");
    track.setAttribute("kind", "subtitles");
    track.setAttribute("label", language);
    track.setAttribute("srclang", index);
    track.setAttribute("src", "/files/"+id+"/"+id+"."+index+".vtt");
    if ( index == "fr"){
      track.setAttribute("default", "");
    }
    video.append(track);
  });
  $("#video").append(video);
  return false;
};

//Show the list
var showList = function(){
  getVideos(function(data){
    $("#current").empty();

    var div = document.getElementById("current");
    if ( data.Items.length ){
      $.each(data.Items, function(k,item){
        var a = document.createElement("a");
        a.setAttribute("class", "list-group-item list-group-item-action flex-column align-items-start");
        a.setAttribute("id", item.Id.S);

        var contentDiv = document.createElement("div");
        contentDiv.setAttribute("class", "d-flex w-100 justify-content-between");

        var title = document.createElement("h5");
        title.setAttribute("class", "mb-1");
        title.append(document.createTextNode(item.FileKey.S))
        contentDiv.append(title);

        var small = document.createElement("small");

        var state = document.createElement("i");
        if ( item.State.S === "DONE" ){
          state.setAttribute("class", "fas fa-play");
        } else {
          state.setAttribute("class", "fas fa-spinner fa-pulse");
        }
        small.append(state);

        contentDiv.append(title);
        contentDiv.append(small);

        var small2 = document.createElement("small");
        small2.append(
          document.createTextNode(item.Id.S + " / " + item.Created.S)
        );

        var statusList = document.createElement("div");
        $.each(SUB.steps, function(k,statusText){
          var small3 = document.createElement("small");
          small3.append(document.createTextNode(statusText));
          if ( statusText === "DONE" ){
            small3.setAttribute("class", "text-success");
            statusList.append(small3);
          } else if ( item.State.S == statusText ){
            small3.setAttribute("class", "text-info");
            statusList.append(small3);
            return false;
          } else {
            statusList.append(small3);
            statusList.append(document.createTextNode(" | "));
          }
        });

        a.append(contentDiv);
        a.append(small2);
        a.append(statusList);

        if ( item.State.S === "DONE" ){
          a.setAttribute("href", "#");
          $(a).click(showVideo);
        }

        div.append(a);
      });
    } else {
      var li = document.createElement("li");
      li.setAttribute("class", "list-group-item");
      li.append(document.createTextNode("No results"));
      div.append(li);
    }
    setTimeout(showList, 500);
  });
};

// Get all videos
var getVideos = function(callback){
  var params = {
    ExpressionAttributeNames: { "#S": "State", },
    ProjectionExpression: "Id, FileKey, Created, #S",
    TableName: "subtitles"
  };
  SUB.dynamo.scan(params).promise().then(function(data){
    return callback(data);
  }).catch(function(err){
    console.log(err, err.stack);
  });
}

// Bind UX components to behaviour
$(document).ready(function(){

  // Load config
  $.getJSON("config.json", function(data){
    AWS.config.update({region: 'us-east-1'});
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
      IdentityPoolId: data.cognitoIdentityPool
    });

    staticBucketArray = data.staticBucket.split(":");
    staticBucket = staticBucketArray[ staticBucketArray.length - 1];

    SUB.staticBucket = new AWS.S3({
      apiVersion: '2006-03-01',
      params: {Bucket: staticBucket}
    });

    mediaBucketArray = data.mediaBucket.split(":");
    mediaBucket = mediaBucketArray[ mediaBucketArray.length - 1];

    SUB.mediaBucket = new AWS.S3({
      apiVersion: '2006-03-01',
      params: {Bucket: mediaBucket}
    });

    SUB.dynamo = new AWS.DynamoDB({ apiVersion: '2012-08-10' });

    // Start polling
    showList();
  });

  $("#refresh").click(showList);

  $("#upload").click(function(){
    SUB.uploadButton.start();
    upload(function(err){
      SUB.uploadButton.stop();
      if (!err){
        $("#refresh").click();
      }
    });
  });

  $("#toggleConstraints").click(function(){
    $("#constraints").toggleClass("d-none");
    $("#constraints i").toggleClass("fa-caret-down");
    $("#constraints i").toggleClass("fa-caret-up");
  });

  // SUB.listButton = Ladda.create(document.querySelector("#refresh"));
  SUB.uploadButton = Ladda.create(document.querySelector("#upload"));

});
