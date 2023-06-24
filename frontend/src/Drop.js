// import React, { useCallback } from 'react'
// import { useDropzone } from 'react-dropzone'

// export default function MyDropzone() {
//     const onDrop = useCallback(acceptedFiles => {
//         const f = acceptedFiles[0]
//         console.log(f)
//         fetch('http://127.0.0.1:8000/upload/', {
//             mode: 'no-cors',
//             method: 'POST',
//             // headers: {
//             //     'Accept': 'application/json',
//             //     'Content-Type': 'application/json',
//             // },
//             body: f,
//             headers: {
//                 'content-type': f.type,
//                 'content-length': `${f.size}`, // 👈 Headers need to be a string
//               },
//         }).then((res) => res.json())
//         .then((data) => console.log(data))
//         .catch((err) => console.error(err));
//     }, [])
//     const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

//     return (
//         <div {...getRootProps()}>
//             <input {...getInputProps()} />
//             {
//                 isDragActive ?
//                     <p>Drop the files here ...</p> :
//                     <p>Drag 'n' drop some files here, or click to select files</p>
//             }
//         </div>
//     )
// }

import 'react-dropzone-uploader/dist/styles.css'
import Dropzone from 'react-dropzone-uploader'

export default function Uploader () {  
  return (
    <Dropzone
      getUploadParams={() => ({ url: 'https://httpbin.org/post' })} // specify upload params and url for your files
      onChangeStatus={({ meta, file }, status) => { console.log(status, meta, file) }}
      onSubmit={(files) => { console.log(files.map(f => f.meta)) }}
      accept="image/*,audio/*,video/*"
    />
  )
}