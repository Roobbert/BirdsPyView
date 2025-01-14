import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import numpy as np
from helpers import Homography, VoronoiPitch, Play, PitchImage, PitchDraw, get_table_download_link
from pitch import FootballPitch
from copy import deepcopy

colors = {'black': '#000000',
          'blue': '#0000ff',
          'brown': '#a52a2a',
          'cyan': '#00ffff',
          'grey': '#808080',
          'green': '#008000',
          'magenta': '#ff00ff',
          'maroon': '#800000',
          'orange': '#ffa500',
          'pink': '#ffc0cb',
          'red': '#ff0000',
          'white': '#ffffff',
          'yellow': '#ffff00'}

st.set_option('deprecation.showfileUploaderEncoding', False)
st.beta_set_page_config(page_title='BirdsPyView', layout='wide')
st.title('Upload Image or Video')
uploaded_file = st.file_uploader("Select Image file to open:", type=["png", "jpg", "mp4"])
pitch = FootballPitch()

if uploaded_file:
    if uploaded_file.type == 'video/mp4':
        play = Play(uploaded_file)
        t = st.slider('You have uploaded a video. Choose the frame you want to process:', 0.0,60.0)
        image = PitchImage(pitch, image=play.get_frame(t))
    else:
        image = PitchImage(pitch, image_bytes=uploaded_file)


    st.title('Pitch lines')

    lines_expander = st.beta_expander('Draw pitch lines on selected image (2 horizontal lines, then 2 vertical lines)',
                                      expanded=True)
    with lines_expander:
        col1, col2, col_, col3 = st.beta_columns([2,1,0.5,1])

        with col1:
            canvas_image = st_canvas(
                fill_color = "rgba(255, 165, 0, 0.3)",
                stroke_width = 2,
                stroke_color = '#e00',
                background_image = image.im,
                width = image.im.width,
                height = image.im.height,
                drawing_mode = "line",
                key = "canvas",
            )

        with col2:
            line_seq = ['U','UP','LG', 'LGA']
            h_line_options = list(pitch.horiz_lines.keys())
            v_line_options = list(pitch.vert_lines.keys())

            hlines = [st.selectbox(f'Horizontal Line #{x+1}', h_line_options,
                      key=f'hline {x}', index=h_line_options.index(line_seq[x]))
                     for x in range(2)]
            vlines = [st.selectbox(f'Vertical Line #{x+1}', v_line_options,
                      key=f'vline {x}', index=v_line_options.index(line_seq[x+2]))
                     for x in range(2)]

        with col3: st.image('pitch.png', width=300)

    if canvas_image.json_data is not None:
        # st.write(canvas_image.json_data["objects"])
        n_lines = len(canvas_image.json_data["objects"])
        with col3: st.write(f'You have drawn {n_lines} lines. Use the Undo button to delete lines.')
        if n_lines>=4:
            image.set_info(pd.json_normalize(canvas_image.json_data["objects"]), hlines+vlines)

            with lines_expander:
                st.write('Converted image:')
                st.image(image.conv_im)  # image conversion

            # --------- Marking players ---------- #
            st.title('Players')
            st.write('Draw rectangle over players on image. '+
                     'The player location is assumed to the middle of the base of the rectangle.')

            p_col1, p_col2, p_col_, p_col3 = st.beta_columns([2,1,0.5,1])

            with p_col2:
                team_color = st.selectbox("Team color: ", list(colors.keys()))
                stroke_color=colors[team_color]
                auto = st.checkbox('Automatically annotate other players')   # option of automatic annotation
                edit = st.checkbox('Edit mode (move selection boxes)')
                update = st.button('Update data')
                original = True #st.checkbox('Select on original image', value=True)

            image2 = image.get_image(original)
            height2 = image2.height
            width2 = image2.width
            with p_col1:
                canvas_converted = st_canvas(
                    fill_color = "rgba(255, 165, 0, 0.3)",
                    stroke_width = 2,
                    stroke_color = stroke_color,
                    background_image = image2,
                    drawing_mode = "transform" if edit else "rect",
                    update_streamlit= update,
                    height = height2,
                    width = width2,
                    key="canvas2",
                )

            if canvas_converted.json_data is not None:

                # --- test section ---  color comparison
                # p1 = canvas_converted.json_data["objects"][0]
                # p2 = canvas_converted.json_data["objects"][1]
                # pitch_array = np.array(image.im.convert("RGBA"))
                # box1 = pitch_array[p1['top']:p1['top']+p1['height']+1, p1['left']:p1['left']+p1['width']+1]
                # box2 = pitch_array[p2['top']:p2['top']+p2['height']+1, p2['left']:p2['left']+p2['width']+1]
                # #st.image(box1)
                # #st.image(box2)
                # m1 = np.mean(box1.reshape(-1,4), 0)
                # m2 = np.mean(box2.reshape(-1,4), 0)
                # st.write(m1,m2)
                # d = np.abs(m1-m2)/m2
                # st.write(np.abs(m1-m2)/m2)
                # st.write(d[:-1])
                # st.write(np.mean(d[:-1]))
                # --------------------

                # --- test section ---  dropping new boxes
                # new_box = deepcopy(canvas_converted.json_data["objects"][0])
                # left = new_box['left']
                # top = new_box['top']
                # height = new_box['height']
                # width = new_box['width']
                # box = canvas_converted.image_data[top:top+height+2, left:left+width+2]  # new box image data
                # nbox = box.reshape(-1, 4)
                # #mean = np.mean(nbox, 0)
                # #st.write(nbox.shape)
                # #st.write(mean)
                # new_box['left'] += 50
                # new_box['top'] -= 0

                # st.write(canvas_converted.json_data["objects"])
                # #canvas_converted.image_data[new_box['top']:new_box['top']+2+height, new_box['left']:new_box['left']+2+width] += box  # Drop a new box (ish)
                # st.write(np.array(image.im.convert("RGBA")).shape)  # pitch image: image.im
                # st.image(canvas_converted.image_data)
                # ---------------------
                p_coord = []  # Create a list of players' attributes, including coordinates
                for player in canvas_converted.json_data["objects"]:
                    coord = {'top': player['top'], 'left': player['left'], 'height': player['height'],
                             'width': player['width'], 'score': -1, 'stroke': player['stroke']}
                    p_coord.append(coord)

                if auto:
                    draw = PitchDraw(image, original=True)
                    pitch_array = np.array(image.im.convert("RGBA"))  # Pitch image in RGBA array
                    p1 = canvas_converted.json_data["objects"][0]  # json_data of the first player annotation
                    team_2 = False
                    p2 = {'width':p1['width'],'height':p1['height']}
                    if len(canvas_converted.json_data["objects"]) > 1:
                        for player in canvas_converted.json_data["objects"][1:]:
                            if player['stroke'] is not p1['stroke']:
                                team_2 = True
                                p2 = player
                                break

                    # Smaller area to reduce background impact    (Future may add sensitivity ------
                    box1 = pitch_array[p1['top']+4:p1['top'] + p1['height'] - 5, p1['left']+3:p1['left'] + p1['width'] - 5]
                    m1 = np.mean(box1.reshape(-1, 4), 0)  # Mean RGBA value within the box
                    if team_2:  # If second team annotation exists:
                        box2 = pitch_array[p2['top'] + 4:p2['top'] + p2['height'] - 5,p2['left'] + 3:p2['left'] + p2['width'] - 5]
                        m2 = np.mean(box2.reshape(-1, 4), 0)

                    # For every point on the image   |   p1: (First) player marked by the user  p2: Second team player (if applicable)
                    for y in range(0, image.im.height - max(p1['height'],p2['height'])):
                        for x in range(0, image.im.width - max(p1['width'],p2['width'])):
                            mean_height = (p1['height']+p2['height'])//2
                            mean_width = (p1['width']+p2['width'])//2
                            converted_coord = image.h.apply_to_points(np.array([x+mean_width/2, y+mean_height/2]).reshape((-1,2)))
                            if (converted_coord / image.h.coord_converter <= 0).any() or \
                                    (converted_coord / image.h.coord_converter >= 100).any():  # If it is outside of the pitch
                                continue  # Invalid point

                            small_box = pitch_array[y+4:y + p1['height'] - 6, x+4:x + p1['width'] - 6]
                            mean_color = np.mean(small_box.reshape(-1,4), 0)
                            diff1 = np.abs(mean_color-m1)/m1
                            if (diff1[:-1] < 0.05).all():  # Possible p1 teammate
                                # ---- Reduce repeating boxes ----
                                score = np.mean(diff1[:-1])
                                overlap = False
                                replace = False
                                for coord in p_coord:
                                    if coord['left'] - coord['width'] + 2 < x < coord['left'] + coord['width'] - 2 \
                                            and coord['top'] - coord['height'] + 2 < y < coord['top'] + coord['height'] - 2 \
                                            and coord['stroke'] is p1['stroke']:
                                        if score < coord['score']:
                                            coord['left'] = x
                                            coord['top'] = y
                                            coord['score'] = score
                                            replace = True
                                            break
                                        overlap = True
                                        break

                                if overlap:
                                    continue

                                if not replace:  # Add a new box
                                    coord = {'top':y, 'left':x, 'height':p1['height'], 'width':p1['width'], 'score':score, 'stroke':p1['stroke']}
                                    p_coord.append(coord)
                                    continue

                            if team_2:  # Possible p2 teammate
                                diff2 = np.abs(mean_color-m2)/m2
                                if (diff2[:-1] < 0.05).all():
                                    # ---- Reduce repeating boxes ----
                                    score = np.mean(diff2[:-1])
                                    overlap = False
                                    replace = False
                                    for coord in p_coord:
                                        if coord['left'] - coord['width'] + 2 < x < coord['left'] + coord['width'] - 2 \
                                                and coord['top'] - coord['height'] + 2 < y < coord['top'] + coord[
                                            'height'] - 2 \
                                                and coord['stroke'] is p2['stroke']:
                                            if score < coord['score']:
                                                coord['left'] = x
                                                coord['top'] = y
                                                coord['score'] = score
                                                replace = True
                                                break
                                            overlap = True
                                            break

                                    if overlap:
                                        continue

                                    if not replace:  # Add a new box
                                        coord = {'top': y, 'left': x, 'height': p2['height'], 'width': p2['width'],
                                                 'score': score, 'stroke': p2['stroke']}
                                        p_coord.append(coord)

                    # Annotate the detected players
                    for coord in p_coord:
                        draw.draw_rect(coord['top'], coord['left'], coord['height'], coord['width'], 'rgb(255, 165, 0)', coord['stroke'])

                    st.image(draw.compose_image())

                if len(canvas_converted.json_data["objects"])>0:
                    dfCoords = pd.json_normalize(p_coord)
                    if original:
                        dfCoords['x'] = (dfCoords['left']+(dfCoords['width'])/2)
                        dfCoords['y'] = (dfCoords['top']+dfCoords['height'])
                        dfCoords[['x', 'y']] = image.h.apply_to_points(dfCoords[['x', 'y']].values)
                    else:
                        dfCoords['x'] = (dfCoords['left']+dfCoords['width'])
                        dfCoords['y'] = (dfCoords['top']+dfCoords['height'])
                    dfCoords[['x', 'y']] = dfCoords[['x', 'y']]/image.h.coord_converter
                    dfCoords['team'] = dfCoords.apply(lambda x: {code: color for color,code in colors.items()}.get(x['stroke']),
                                                      axis=1)
                    # st.write(dfCoords)  # ----------------------------------

                with p_col3:
                    st.write('Player Coordinates:')
                    st.dataframe(dfCoords[['team', 'x', 'y']])


                # --------- Final Output --------- #
                st.title('Final Output')
                voronoi = VoronoiPitch(dfCoords)
                sensitivity = int(st.slider("Sensitivity (decrease if it is drawing over the players; "+
                                            "increase if the areas don't cover the whole pitch)"
                                            , 0, 30, value=10)*2.5)
                o_col1, o_col2, o_col3 = st.beta_columns((3,1,3))
                with o_col2:
                    show_voronoi = st.checkbox('Show Voronoi', value=True)
                    voronoi_opacity = int(st.slider('Voronoi Opacity', 0, 100, value=20)*2.5)
                    player_highlights = st.multiselect('Players to highlight', list(dfCoords.index))
                    player_size = st.slider('Circle size', 1, 10, value=2)
                    player_opacity = int(st.slider('Circle Opacity', 0, 100, value=50)*2.5)
                with o_col1:
                    draw = PitchDraw(image, original=True)
                    if show_voronoi:
                        draw.draw_voronoi(voronoi, image, voronoi_opacity)
                    for pid, coord in dfCoords.iterrows():
                        if pid in player_highlights:
                            draw.draw_circle(coord[['x','y']].values, coord['team'], player_size, player_opacity)
                    st.image(draw.compose_image(sensitivity))
                with o_col3:
                    draw = PitchDraw(image, original=False)
                    for pid, coord in dfCoords.iterrows():
                        draw.draw_circle(coord[['x','y']].values, coord['team'], 2, player_opacity)
                        draw.draw_text(coord[['x','y']]+0.5, f"{pid}", coord['team'])
                    st.image(draw.compose_image(sensitivity))

                st.markdown(get_table_download_link(dfCoords[['team', 'x', 'y']]), unsafe_allow_html=True)

