import React, { Component } from 'react';
import Markdown from 'markdown-to-jsx';
import { Divider } from 'antd';
import TeX from '@matejmazur/react-katex';
import md5 from 'blueimp-md5';
import './css/md.css';
import 'katex/dist/katex.min.css';


let citations = {};
let related_links = {};
let figures = {};
let tables = {};
let equations = {};

class MdPage extends Component{
    state = {
        md_content : ''
    }

    componentWillMount(){
        const { md_content } = this.props;
        this.setState({
            md_content
        });
        citations = {};
        related_links = {};
        figures = {};
        tables = {};
    }

    addRelatedLink = (children, ...props )=>{
        const href = children.href;
        const title = children.children.join("")
        const items = title + "|" + href;
        if(items in related_links){
            return [<a href={href}>{title}</a>,<sup><a href={'#' + md5(items)}>{related_links[items]}</a></sup>]
        }else{
            related_links = {...related_links,[items]: Object.keys(related_links).length + 1};
            return [<a href={href}>{title}</a>, <sup><a href={'#' + md5(items)}>{related_links[items]}</a></sup>]
        }   
    }

    addCite = (children, ...props) =>{
        const ref = children.children.join("")
        if(!(ref in citations)){
            citations = {
                ...citations, 
                [ref]: Object.keys(citations).length + 1
            }
        }        
        return [<a href={'#' + md5(ref)} className="done">[{citations[ref]}]</a>]
    }

    addTable = ({children, ...props}) =>{
        return <div>
            <table style={{display: 'table', textAlign: 'center'}}>
                {children}
            </table>
            </div>
    }

    addTableCaption = ({children, ...props}) =>{
        const {name} = props;
        if(!(name in tables)){
            tables = {
                ...tables,
                [name]: Object.keys(tables).length + 1
            }
        }
        return <div>
            <p style={{textAlign:"center"}}>表:{tables[name]}{name} </p>
            </div>
    }

    addEquations = ({children})=>{
        const equ = children.join("");
        if(!(equ in equations)){
            equations = {
                ...equations,
                [equ]: Object.keys(equations).length + 1
            }
        }
        return <div style={{position: "relative"}}>
                    <TeX>{equ}</TeX>
                    <div style={{position: "absolute", top: '-2px', right: '5px'}}>({equations[equ]})</div>
                </div>
                
    }

  

    addImage = ({children, ...props}) => {
        const url = props.src;
        const alt = props.alt;
        if(!(url in figures)){
            figures = {
                ...figures,
                [url]: Object.keys(figures).length + 1
            }
        }
        const width = props.width ? props.width : "80%";
        const margin_left = (100 - parseInt(width, 10)) /2;
        return <div>
                <img src={url} width={width} style={{marginLeft: margin_left + "%"}} alt={url}/>
                <p style={{textAlign:"center"}}>图{figures[url]}：{alt}</p>
                </div>
    }

    componentDidMount(){
        this.forceUpdate();
    }


    render() {
        return <div className="markdown-body">  
            <Markdown 
                children={this.state.md_content}
                options = {{
                    overrides: {
                        a: this.addRelatedLink,
                        img: this.addImage,
                        cite: this.addCite,
                        table: this.addTable,
                        tablecaption: this.addTableCaption,
                        equation: this.addEquations,
                    }
                }}  
            />
            {Object.keys(related_links).length > 0 &&<div>
                <Divider orientation="right">
                    Related Links
                </Divider>
                {Object.keys(related_links).map((item, index)=>{
                    const pku = item.split("|");
                    return <p key={index} id={"#"+md5(item)}>{index + 1} : {pku[0]} {pku[1]}</p>
                })}
            </div>

                
            }

            {Object.keys(citations).length > 0 &&<div>
                <Divider orientation="right">
                    References
                </Divider>

                {Object.keys(citations).map((item, index)=>{
                    const v = citations[item]
                    return <p key={index} id={"#" + md5(v)}>[{index + 1}]: {item}</p>
                })}
            </div>
            }
            </div>
    }
}

export default MdPage;
