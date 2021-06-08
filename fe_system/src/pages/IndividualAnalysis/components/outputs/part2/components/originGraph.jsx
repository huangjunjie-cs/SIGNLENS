import React , {Component} from 'react';

import "./graph.css";

class OriginGraph extends Component {


  handleLineClick = (x, y)=>{
    const { handleXYChange } = this.props;
    handleXYChange(x, y);
  }

  render(){
    const {name_dict, node_list, links, key} = this.props;
    const margin = 20;
    const width = 200;
    let node_dict = {}

    const nodes = node_list.map(item=>{
      node_dict[item[0]] = {x : item[1][0] * width/2 + width/2, y: item[1][1]*width/2 + width/2}
      return <text x={item[1][0] * width/2 + width/2 - width/12} y={item[1][1]*width/2 + width/2} fontFamily="Verdana" fontSize="10">
               {name_dict[item[0]]}
             </text>
    })

    const lines = links.map(item=>{
      const node1 = node_dict[item.source]
      const node2 = node_dict[item.target]
      if(item.weight > 0){
        const text_pos = {x: (node1.x + node2.x) /2, y:(node1.y + node2.y) /2};
        return [<line
                  x1={node1.x} 
                  y1={node1.y} 
                  x2={node2.x} 
                  y2={node2.y}
                  onClick={()=>this.handleLineClick(item.source, item.target)} 
                  className="line-green" 
                />,
                 <text
                    x={text_pos.x} 
                    y={text_pos.y} 
                    fill= "rgb(0,255,0)" 
                    font-size="10"
                  >
                  {item.weight.toFixed(1)}
                 </text>
               ]
        
      }else if(item.weight < 0){
        const text_pos = {x: (node1.x + node2.x) /2, y:(node1.y + node2.y) /2};
        return [<line 
                  x1={node1.x} 
                  y1={node1.y} 
                  x2={node2.x} 
                  y2={node2.y}
                  x={item.source}
                  y={item.target}
                  onClick={()=>this.handleLineClick(item.source, item.target)} 
                  className="line-red" 
                />,
                <text
                    x={text_pos.x} 
                    y={text_pos.y} 
                    fill= "rgb(255,0,0)" 
                    font-size="10"
                  >
                  {item.weight.toFixed(1)}
                </text>
              ]
        
      }else{
        return <line 
                  x1={node1.x} 
                  y1={node1.y} 
                  x2={node2.x}
                  y2={node2.y}
                  x={item.source}
                  y={item.target}
                  onClick={()=>this.handleLineClick(item.source, item.target)} 
                  className="line"
                />
      }
    })
    return <div key={key}>
        <svg width={width + margin*2} height={width + margin*2} key={key}>
          <g transform={"translate(" + margin/2 + "," + margin/2 + ")"}>
            {lines}
            {nodes}
          </g>
        </svg>
      </div>
  }
}

export default OriginGraph;
