import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import G6 from '@antv/g6';
import { size } from 'lodash';
const nodes =  [{ group: 1, id: '1762', label: 'Wang AnShi', name: '王安石' },
      { group: 2, id: '1493', label: 'Su Zhe', name: '苏辙' },
      { group: 2, id: '3762', label: 'Su Xun', name: '苏洵' },
      { group: 1, id: '1384', label: 'Ouyang Xiu', name: '欧阳修' },
      { group: 1, id: '7364', label: 'Zeng Gong', name: '曾鞏' },
      { group: 2, id: '3767', label: 'Su Shi', name: '苏轼' }];
const edges = [
    { value: 4.0, source: '1493', target: '1384' },
    { value: 4.0, source: '1384', target: '1493' },
    { value: 6.0, source: '1493', target: '3767' },
    { value: 6.0, source: '3767', target: '1493' },
    { value: -1.0, source: '1493', target: '1762' },
    { value: -1.0, source: '1762', target: '1493' },
    { value: 3.0, source: '1493', target: '3762' },
    { value: 3.0, source: '3762', target: '1493' },
    { value: 1.0, source: '1762', target: '7364' },
    { value: 1.0, source: '7364', target: '1762' },
    { value: 0.0, source: '1762', target: '3767' },
    { value: 0.0, source: '3767', target: '1762' },
    { value: 4.0, source: '1762', target: '1384' },
    { value: 4.0, source: '1384', target: '1762' },
    { value: 10.0, source: '3767', target: '1384' },
    { value: 10.0, source: '1384', target: '3767' },
    { value: 4.0, source: '3767', target: '3762' },
    { value: 4.0, source: '3762', target: '3767' },
    { value: 0.0, source: '3767', target: '7364' },
    { value: 0.0, source: '7364', target: '3767' },
    { value: 1.0, source: '7364', target: '3762' },
    { value: 1.0, source: '3762', target: '7364' },
    { value: 7.0, source: '7364', target: '1384' },
    { value: 7.0, source: '1384', target: '7364' },
    { value: 5.0, source: '3762', target: '1384' },
    { value: 5.0, source: '1384', target: '3762' },
];

const data = {
    nodes: nodes,
    edges: edges
}

const colorMaps = ["#1f77b4",
"#aec7e8",
"#ff7f0e",
"#ffbb78",
"#2ca02c",
"#98df8a",
"#d62728",
"#ff9896",
"#9467bd",
"#c5b0d5",
"#8c564b",
"#c49c94",
"#e377c2",
"#f7b6d2",
"#7f7f7f",
"#c7c7c7",
"#bcbd22",
"#dbdb8d",
"#17becf",
"#9edae5"]

export default function () {
  const ref = React.useRef(null);
  let graph = null;

  useEffect(() => {
    if (!graph) {
      graph = new G6.Graph({
        container: ReactDOM.findDOMNode(ref.current),
        width: 800,
        height: 600,
        "fitView": true,
        "fitViewPadding": [
          16,
          16,
          16,
          16
        ],
      "layout": {
        "type": "force",
        "center": [
          400,
          300
        ],
        "linkDistance": 50,
        "nodeStrength": -30,
        "edgeStrength": false,
        "nodeSize": 20,
        "nodeSpacing": 0,
        "preventOverlap": true
      },
      "defaultNode": {
        "type": "circle",
        "style": {
          "stroke": "rgb(79, 125, 241)"
        },
        "linkPoints": {
          "fill": "rgb(19, 30, 51)"
        },
        "labelCfg": {
          "style": {
            "fontSize": 5,
            "style": {
              "fill": "rgb(255, 255, 255)",
            }
          }
        }
      },
      "defaultEdge": {
        "type": "line",
        "style": {
          "stroke": "rgb(79, 79, 79)"
        }
      },
      });
    }
    const edges = data.edges;
    edges.forEach((edge) => {
      if (!edge.style) {
        edge.style = {};
      }
      let v = edge.value > 0 ? edge.value : -1 * edge.value;
      edge.style.lineWidth = v; // 边的粗细映射边数据中的 weight 属性数值

      if(edge.value > 0){
        edge.style.stroke = 'green';
      }else{
        edge.style.stroke = 'red';

      }
    });

    const nodes = data.nodes;
    nodes.forEach((node)=>{
      if (!node.style) {
        node.style = {};
      }
      node.style.fill=colorMaps[node.group]
    })
    console.log(data);
    graph.data(data);
    graph.render();
  }, []);

  return <div ref={ref}></div>;
}