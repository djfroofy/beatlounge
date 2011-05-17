var bluez = function() {
  var api = {};

  /* utils */
  function divmod(num, div){ return [Math.floor(num/div), num%div]}
  function Cell(row, col) {
    this.row = row;
    this.col = col;
  }
  api.Cell = Cell;
  function drawRect(context, x, y, w, h) {
    context.beginPath();
    context.rect(x,y,w,h);
    context.closePath();
    context.stroke();
  }
  api.drawRect = drawRect;

  /* WebSocketCanvasGrid proto */
  function WebSocketCanvasGrid() {}
  WebSocketCanvasGrid.prototype.defaultOptions = {
    // TODO: the defaultz are sucking... need better pattern.
    "wsHost": location.hostname,
    "wsPort": 8347
  }
  WebSocketCanvasGrid.prototype.__init__ = function(canvas, options) {
    var self = this;
    if (typeof options == 'object') {
  		options = $.extend(self.defaultOptions, options);
  	} else {
  		options = self.defaultOptions;
  	}
    self.options = options;
    self.ws = new WebSocket("ws://"+options["wsHost"]+":"+options["wsPort"]+options["wsPath"]);
    self.canvas = canvas;
    self.ctx = self.canvas.getContext('2d');
    self.ctx.strokeStyle = self.options["strokeStyle"];
    self.BoardWidth = self.options["BoardWidth"]
    self.BoardHeight = self.options["BoardHeight"]
    self.PieceWidth = self.options["PieceWidth"]
    self.PieceHeight = self.options["PieceHeight"]
    self.PixelWidth = self.PieceWidth * self.BoardWidth + 1;
    self.PixelHeight = self.PieceHeight * self.BoardHeight + 1;
    self.canvas.id = self.options["id"];
    self.canvas.width = self.PixelWidth;
    self.canvas.height = self.PixelHeight;
    self.defaultLevel = self.options["defaultLevel"];

  }
  WebSocketCanvasGrid.prototype.getCursorPosition = function(e){
    var self = this;
    var x;
    var y;
    if (e.pageX != undefined && e.pageY != undefined) {
      x = e.pageX;
      y = e.pageY;
    }
    else {
    	x = e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
      y = e.clientY + document.body.scrollTop + document.documentElement.scrollTop;
    }
    x -= e.currentTarget.offsetLeft;
    y -= e.currentTarget.offsetTop;
    x = Math.min(x, self.BoardWidth * self.PieceWidth);
    y = Math.min(y, self.BoardHeight * self.PieceHeight);
    var cell = new Cell(Math.floor(y/self.PieceHeight), Math.floor(x/self.PieceWidth));
    return cell;
  }

  LevelRoller.prototype = new WebSocketCanvasGrid;
  LevelRoller.prototype.constructor = LevelRoller;
  function LevelRoller(canvas, options){
    var self = this;
    self.defaultOptions = {
      "id": "level",
      "strokeStyle": "#000",
      "defaultLevel": 100,
      "BoardWidth": 24*16,
      "BoardHeight": 128,
      "PieceWidth": 3,
      "PieceHeight": 1,
      "wsPath": "/vol"
    };
    // TODO: need to work out a better default options scheme.
    // this like overwrites the proto defaults
    self.defaultOptions = $.extend(self.constructor.prototype.defaultOptions, self.defaultOptions);
    self.__init__(canvas, options);

    self.selected = {};
    self.dragging = false;
    self.lastcol = undefined; // Too know what direction we are dragging
  
    function draw() {
      var value;
      self.ctx.clearRect(0, 0, self.PixelWidth, self.PixelHeight);
      drawRect(self.ctx, 0, 0, self.PixelWidth, self.PixelHeight);
      for (i = 0; i < self.BoardWidth; i++){
        if (self.selected[i] == undefined){
          self.selected[i] = self.defaultLevel;
          value = self.defaultLevel;
        } else {
          value = self.selected[i];
        }
        drawRect(self.ctx, i*self.PieceWidth, self.BoardHeight - value, self.PieceWidth, self.PieceHeight);
      }
    }
    self.draw = draw;
  
    self.drag = function(e) {
      var cell = self.getCursorPosition(e);
      var difference = cell.col - self.lastcol;
      var level = self.BoardHeight - cell.row;
      self.selected[cell.col] = level;
      if (Math.pow(difference, 2) > 1){
        for (i=self.lastcol; i <cell.col; i++){
          self.selected[i] = level;
        }
        for (i=self.lastcol; i > cell.col; i--){
          self.selected[i] = level;
        }
      }
      self.lastcol = cell.col;
      msg = JSON.stringify(self.selected);
      self.ws.send(msg);
      self.draw();
    };

    self.mousedown = function(e){
      var cell = self.getCursorPosition(e);
      self.lastcol = cell.col;
      var level = self.BoardHeight - cell.row;
      self.selected[cell.col] = level;
      self.dragging = true;
      self.canvas.onmousemove = self.drag;
      self.selected[cell.col] = level;
      self.draw();
    };
    self.mouseup = function(e){
      self.canvas.onmousemove = null;
      self.dragging = false;
    };
    self.canvas.onmousedown = self.mousedown;
    self.canvas.onmouseup = self.mouseup;

    self.ws.onmessage = function(e){
      //console.log(e);
      //self.selected = JSON.parse(e.data);
      //self.draw();
    };
    self.ws.onopen = function(e){
      console.log("open");
    };
    self.ws.onerror = function(e){
      console.log("error");
    };
    self.ws.onclose = function(e){
      console.log("close");
    };
  }
  api.LevelRoller = LevelRoller;


  RainbowSequencer.prototype = new WebSocketCanvasGrid;
  RainbowSequencer.prototype.constructor = RainbowSequencer;
  function RainbowSequencer(canvas, options) {
    var self = this;
    self.defaultOptions = {
      "id": "step",
      "BoardWidth": 24*16,
      "BoardHeight": 88,
      "PieceWidth": 3,
      "PieceHeight": 8,
      "wsPath": "/step"
    };
    self.defaultOptions = $.extend(self.constructor.prototype.defaultOptions, self.defaultOptions);
    self.__init__(canvas, options);

    function initSelected(){
      self.selected = []
      for (var i = 0; i < self.BoardHeight; i++){
        self.selected.push([]);
        for (var j = 0; j < self.BoardWidth; j++){
          self.selected[i].push(0);
        }
      }
    }
    initSelected();

    function draw() {
      self.ctx.clearRect(0, 0, self.PixelWidth, self.PixelHeight);
      self.ctx.beginPath();
      /* vertical lines */
      for (var x = 0; x <= self.PixelWidth; x += self.PieceWidth) {
        self.ctx.moveTo(0.5 + x, 0);
        self.ctx.lineTo(0.5 + x, self.PixelHeight);
      }
      /* horizontal lines */
      for (var y = 0; y <= self.PixelHeight; y += self.PieceHeight) {
        self.ctx.moveTo(0, 0.5 + y);
        self.ctx.lineTo(self.PixelWidth, 0.5 +  y);
      }
      self.ctx.strokeStyle = "#ccc";
      self.ctx.stroke();

      /* make some verticle rectangles to see */
      for (var i = 0; i < self.BoardWidth; i ++) {
        self.ctx.fillStyle = "#fff";
        if (i % 3 == 0) {
          self.ctx.fillStyle = "#ccc";
        }
        // 8th triplet
        if (i % 4 == 0) {
          self.ctx.fillStyle = "#def";
        }
        // 16th
        if (i % 6 == 0) {
          self.ctx.fillStyle = "#bbb";
        }
        // qt triplet
        if (i % 8 == 0) {
          self.ctx.fillStyle = "#abc";
        }
        // 8th
        if (i % 12 == 0) {
          self.ctx.fillStyle = "#aaa";
        }
        // qt
        if (i % 24 == 0) {
          self.ctx.fillStyle = "#999";
        }
        if (i % 24 == 0) {
          self.ctx.fillStyle = "#888";
        }
        // whole
        if (i % (24*4) == 0) {
          self.ctx.fillStyle = "#777";
        }
        // 2 whole
        if (i % (24*8) == 0) {
          self.ctx.fillStyle = "#555";
        }
        self.ctx.fillRect(i*self.PieceWidth, 0, self.PieceWidth, self.PixelHeight);
      }

      /* horizontal rectangles, notes */

      var wheel = {
        9: "rgba(255, 0, 0, .2)",  
        4: "rgba(255, 127, 0, .2)",
        11: "rgba(255, 255, 0, .2)",
        6: "rgba(127, 255, 0, .2)",
        1: "rgba(0, 255, 0, .2)",
        8: "rgba(0, 255, 127, .2)",
        3: "rgba(0, 255, 255, .2)",
        10: "rgba(0, 127, 255, .2)",
        5: "rgba(0, 0, 255, .2)",
        0: "rgba(127, 0, 255, .2)",
        7: "rgba(255, 0, 255, .2)",
        2: "rgba(255, 0, 127, .2)",
      };
      for (var i = self.BoardHeight; i > 0; i--){
        self.ctx.fillStyle = wheel[(self.BoardHeight-i)%12];
        self.ctx.fillRect(0, (self.BoardHeight-i)*self.PieceHeight, self.PixelWidth, self.PieceHeight);
      }

      // selected
      for (var i = 0; i < self.BoardHeight; i++){
        for (j = 0; j < self.BoardWidth; j++){
          if (self.selected[i][j] === 1){
            self.drawPiece(new Cell(i,j));
          }
        }
      }
    } /* draw */
    self.draw = draw;

    function drawPiece(cell) {
      var col = cell.col;
      var row = cell.row;
      var x = (col * self.PieceWidth) + (self.PieceWidth/2);
      var y = (row * self.PieceHeight) + (self.PieceHeight/2);
      var radius = (self.PieceWidth/2) - (self.PieceWidth/10);
      self.ctx.beginPath();
      self.ctx.arc(x, y, radius, 0, Math.PI*2, false);
      self.ctx.closePath();
      self.ctx.strokeStyle = "#000";
      self.ctx.stroke();
	    self.ctx.fillStyle = "#000";
      self.ctx.fill();
    }
    self.drawPiece = drawPiece;

    self.canvas.onclick = function(e){
      var cell = self.getCursorPosition(e);
      var selecting = self.selected[cell.row][cell.col] === 0;
      if (selecting) {
        self.selected[cell.row][cell.col] = 1;
      } else {
        self.selected[cell.row][cell.col] = 0;
      }
      //console.log(cell, selecting);
      col = [];
      for (var i=0; i < self.BoardHeight; i++){
        if (self.selected[i][cell.col] === 1){
          col.push(self.BoardHeight-i);
        }
      }
      //console.log(cell.col, col);
      self.ws.send(cell.col + "-" + col);
    }
  
    self.ws.onmessage = function(e) {
      console.log(e);
      var o = JSON.parse(e.data);
      //console.log(o);
      initSelected();
      for (var tick in o){
        if (o.hasOwnProperty(tick)){
          for (var i=0; i < o[tick].length; i++){
            note = o[tick][i];
            self.selected[(self.BoardHeight-note)][tick] = 1;
          }
        }
      }
      self.draw();
    }

    self.ws.onopen = function(e){
      console.log("open");
    };
    self.ws.onerror = function(e){
      console.log("error");
    };
    self.ws.onclose = function(e){
      console.log("close");
    };

  } /* RainbowSequencer */
  api.RainbowSequencer = RainbowSequencer;

  return api;
}();

