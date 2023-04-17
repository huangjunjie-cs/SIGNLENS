import React, { Component } from 'react';
import { Table } from 'antd';

class LinkInfo extends Component {
  render() {
    const { x, y, relations } = this.props;
    const columns = [
      { title: 'X', width: 100, dataIndex: 'X', key: 'X', fixed: 'left', align: 'center' },
      { title: 'Y', width: 100, dataIndex: 'Y', key: 'Y', fixed: 'left', align: 'center' },
      { title: 'Sign', width: 100, dataIndex: 'Sign', key: 'Sign', align: 'center' },
      { title: 'Time', width: 100, dataIndex: 'Time', key: 'Year', align: 'center' },
      {
        title: 'Note',
        dataIndex: 'Info',
        key: 'Info',
        align: 'center',
        render: (data) => {
          const obj = JSON.parse(data);
          console.log(obj);
          return Object.entries(obj).map((item) => <div>{`${item[0]}:${item[1]}`}</div>);
        },
      },
    ];
    const data = relations;
    return (
      <div>
        <div>
          <span className="people-selected">{`${x}`}</span> and{' '}
          <span className="people-selected">{`${y}`}</span> are selected
        </div>
        <div>
          <Table
            size="small"
            columns={columns}
            dataSource={data}
            scroll={{ x: 850 }}
            pagination={false}
          />
        </div>
      </div>
    );
  }
}
export default LinkInfo;
