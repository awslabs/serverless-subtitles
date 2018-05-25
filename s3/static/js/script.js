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

class Step extends React.Component{
  render(){
    const item = this.props.item;
    const step = this.props.step;
    if ( item.State.S == step && step === "DONE" ){
      return( <small className="text-success">{step}</small> )
    } else if ( item.State.S == step ){
      return ( <small className="text-info">{step} </small> )
    } else if ( SUB.steps.indexOf(step) < SUB.steps.indexOf(item.State.S) ) {
      return ( <small> {step} | </small> )
    } else {
      return (null)
    }
  }
}

class Steps extends React.Component{
  render(){
    const item = this.props.item;
    const steps = SUB.steps.map((step) =>
      <Step item={item} step={step} key={step}/>
    );
    return (
      <div>{steps}</div>
    );
  }
}

class IconState extends React.Component{
  constructor(props){
    super(props);
    this.state = {state: props.state};
  }
  update(){
    this.setState(function(prevState, props) {
      return {
        state: props.state
      };
    });
  }
  componentDidMount() {
    this.timerID = setInterval(
      () => this.update(),
      500
    );
  }
  componentWillUnmount() {
    clearInterval(this.timerID);
  }
  render(){
    if ( this.state.state === "DONE" ){
      return (<i className="fas fa-play"></i>)
    } else {
      console.log("STATE", this.state.state);
      return (<i className="fas fa-spinner fa-pulse"></i>)
    }
  }
}

class Item extends React.Component{
  render(){
    const item = this.props.item;
    return(
      <a className="list-group-item list-group-item-action flex-column align-items-start"
      id={this.props.item.Id.S} key={this.props.item.Id.S} href="#" onClick={showVideo}>
        <div className="d-flex w-100 justify-content-between">
          <h5 className="mb-1">{this.props.item.FileKey.S}</h5>
          <small>
            <IconState state={this.props.item.State.S} />
          </small>
        </div>
        <small>{this.props.item.Id.S} / {this.props.item.Created.S}</small>
        <Steps item={this.props.item} />
      </a>
    )
  }
}

class ItemList extends React.Component{
  constructor(props){
    super(props);
    this.state = {items: props.list.Items};
  }
  update(){
    getVideos(function(data){
      this.setState({
        items: data.Items
      });
    }.bind(this));
  }
  componentDidMount() {
    this.timerID = setInterval(
      () => this.update(),
      500
    );
  }
  componentWillUnmount() {
    clearInterval(this.timerID);
  }
  render(){
    if ( this.state.items.length ){
      const listItems = this.state.items.map((item) =>
        <Item item={item} key={item.Id.S}/>
      );
      return (
        <div>{listItems}</div>
      )
    } else {
      return (
        <li className="list-group-item">No results</li>
      )
    }
  }
}

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
    ReactDOM.render(
      <ItemList list={data}/>,
      document.getElementById('current-react')
    );
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

    var staticBucketArray = data.staticBucket.split(":");
    var staticBucket = staticBucketArray[ staticBucketArray.length - 1];

    SUB.staticBucket = new AWS.S3({
      apiVersion: '2006-03-01',
      params: {Bucket: staticBucket}
    });

    var mediaBucketArray = data.mediaBucket.split(":");
    var mediaBucket = mediaBucketArray[ mediaBucketArray.length - 1];

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
