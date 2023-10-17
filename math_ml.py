import requests
import base64
import cv2

url = 'https://api.mathpix.com/v3/text'
app_id = 'siby_sebastian_magicsw_com_secure'
app_key = '47252dbebd2a29ddd3ee701d4691d6bcb0aa94c6c2b869f0850e9470e301bda3'

# Request headers
headers = {
    'app_id': app_id,
    'app_key': app_key,
    'Content-type': 'application/json'
}

# List of allowed LaTeX symbols
latex_symbols = [
    "-","+","\\times", "\\pm", "\\mp", "\\div", "\\cdot", "\\neq", "\\geq", "\\leq", "\\theta", "\\lambda", "\\mu", "\\pi",
    "=", "<", ">", "_",
    "^", "|", "\\infty", "\\div", "\\sqrt", "\\pm", "\\mp", "\\cdot",
    "\\neq", "\\geq", "\\leq", "\\theta", "\\lambda", "\\mu", "\\pi",
    "\\alpha", "\\beta", "\\gamma", "\\phi", "\\Sigma", "\\Omega",
    "\\nabla", "\\int", "\\sum", "\\prod", "\\subset", "\\cup", "\\cap",
    "\\rightarrow", "\\leftarrow", "\\Rightarrow", "\\Leftarrow",
    "\\leftrightarrow", "\\Leftrightarrow", "= -", "\\frac", "\\emptyset","\\text","\\quad"
]

symbols_to_remove=["\\cdot","\\left","\\right","\\times","\\mathrm","{","}","\\text","\\quad","\\frac","^"]



def is_number(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def callMathpixAPI(file_path):
        with open(file_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Request body
        data = {
                'src': 'data:image/png;base64,' + image_data,
                "formats": ["text", "data", "html", "latex_styled","math"],
                "include_asciimath": True,
                 "include_line_data": True,
                "include_latex": True,
                "include_mathml": True
            }


        # Send the POST request to the Mathpix API
        response = requests.post(url, json=data, headers=headers)
        result = response.json()
        print('JSON:',result)
        return result


def findMathCoordinates(result,rgb):
    final_arr=[]
    errorObj = result.get('error')
    
    if errorObj is not None and 'Image too large' == errorObj:
        print('error image is large')
        raise ValueError("Image too large")
        
    for word_entry in result['line_data']:
        print("\n")
        # line_number = line_number + 1
        if 'text' in word_entry:
            cnt_word = word_entry['text']
            contains_math = any(symbol in cnt_word for symbol in latex_symbols)
            contains_numbers = any(is_number(char) for char in cnt_word)

            # the line will contain mathml if it has math symbols and numbers
            if contains_math and contains_numbers:
                latex_line = word_entry.get('text').strip()
                # replace all the latex symbols with empty string
                for i in symbols_to_remove:
                    if i=="{" or i=="}":
                        latex_line = latex_line.replace(i,"")
                        continue
                    latex_line = latex_line.replace(i," ")
                # if the type is math then no need to change the coordinates
                if "math" in word_entry.get('type'):
                    cv2.rectangle(rgb, word_entry['cnt'][0], word_entry['cnt'][2] , (0, 0, 255), 1)
                    pass
                # if the type is text then we need to change the coordinates
                else:           
                    while True:
                        # mathml will be inside \( \)
                        if "\\(" in latex_line :
                            x1 = latex_line.index("\\(")
                        else:
                            break
                        
                        print('x1 chars before bracket : '+ str(x1)+" " + latex_line)
                        c1 = word_entry['cnt'][0]
                        print("c1 before ", c1)

                        latex_line = latex_line.replace("\\( ","",1)
                        # latex_line = latex_line.replace("  "," ")

                        if "\\)"in latex_line :
                            x2 = latex_line.index("\\)")-1
                        else:
                            x2 = 0
                        
                        if x2-x1<4:
                            continue
                        print('x2 chars : '+str(x2))

                        latex_line = latex_line.replace(" \\)","",1)

                        
                        height=word_entry['cnt'][0][1]-word_entry['cnt'][1][1]
                        print("height : ",height)   

                        if height<=40 and x1>=39:
                            factor=8.2
                        elif height<=40 and x1<39:
                            factor=8.4
                        elif height>40 and x1>=39:
                            factor=8.4
                        else:
                            factor=9
                        


                        print("factor : ",factor)

                        if latex_line.startswith("\n"):
                            x1 = (x1*factor)
                            x2 = (x2*factor)
                            print("with \\n")
                        else:
                            x1 = (x1*factor)
                            x2 = (x2*factor)
                            print("without \\n")
                        
                        x1 = int(x1)
                        x2 = int(x2)
                        # adjusting the position of x1
                        initial_x1 = c1[0]

                        # word_entry['cnt'][0] = [c1[0]+x1,c1[1]-3]
                        # c1 = word_entry['cnt'][0]
                        c1=[initial_x1+x1,c1[1]-4]

                        
                        c2 = word_entry['cnt'][2]
                        print("c2 before ",word_entry['cnt'][2] )
                        
                        if initial_x1+x2<=word_entry['cnt'][2][0]:
                            # adjusting the position of x2  
                            # word_entry['cnt'][2] = [initial_x1+x2,c2[1]+2]
                            # c2 = word_entry['cnt'][2]
                            c2=[initial_x1+x2,c2[1]+1]

                        print("c1 after ",word_entry['cnt'][0] )
                        print("c2 after ",word_entry['cnt'][2] )
                        cv2.rectangle(rgb,c1,c2, (0, 0, 255), 1)

                            #   x1, x2, y1, y2
                        # coordinates=[cnt_data[0][0],cnt_data[2][0],cnt_data[1][1],cnt_data[0][1]]
                        # cnt_data = word_entry['cnt']
                        top=c2[1]
                        left=c1[0]
                        width=c2[0]-c1[0]
                        height=c1[1]-c2[1]
                        final_arr.append([top,left,height,width])
    
    cv2.imwrite('final.png',rgb)
    # print(final_arr)
    return final_arr
                        
def mathpixAPI(file_path):
        result = callMathpixAPI(file_path)
        rgb = cv2.imread(file_path)
        try:
            return findMathCoordinates(result,rgb)
        except ValueError as e:
            print(f"Error {e}")
            return None

        
if __name__ == '__main__':
    print(mathpixAPI('math_1.jpg'))
            
    