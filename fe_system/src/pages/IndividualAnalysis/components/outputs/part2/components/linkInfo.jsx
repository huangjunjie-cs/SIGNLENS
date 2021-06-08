import React , {Component} from 'react';
import { Table } from 'antd';

class LinkInfo extends Component {
    render(){
        const {x, y, relations} = this.props;
        const columns = [
            {title: 'X', width:100, dataIndex: 'X', key: 'X', fixed: 'left', align:'center'},
            {title: 'Y', width:100, dataIndex: 'Y', key: 'Y', fixed: 'left', align:'center'},
            {title: 'AssocName', width:200, dataIndex: 'AssocName', key: 'AssocName', align:'center'},
            {title: 'Year', width:100, dataIndex: 'Year', key: 'Year', align:'center'},
            {title: 'TextTitle', width:200, dataIndex: 'TextTitle', key: 'TextTitle', align:'center'},
            {title: 'Source', width:200, dataIndex: 'Source', key: 'Source', align:'center'},
            {title: 'Pages', width:100, dataIndex: 'Pages', key: 'Pages', align:'center'},
            {title: 'Notes', width:300, dataIndex: 'Notes', key: 'Notes', align:'center'},
        ]
        const data = relations;
        return <div>
            <div><span className="people-selected">{`${x}`}</span> and <span className="people-selected">{`${y}`}</span> are selected</div>
            <div>
            <Table
                size="small"
                columns={columns}
                dataSource={data}
                scroll={{ x: 1350 }} 
                pagination={false}
            />
            </div>
        </div>
    }
    
}   
export default LinkInfo;