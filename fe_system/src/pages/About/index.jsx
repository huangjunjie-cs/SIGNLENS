import React from 'react';
import MdPage from '@/components/MdPage';


const intro_md = `

## Introduction

`


class Introduction extends React.Component {

    render(){
        return <MdPage md_content={intro_md} />;
    }
}

export default Introduction;
