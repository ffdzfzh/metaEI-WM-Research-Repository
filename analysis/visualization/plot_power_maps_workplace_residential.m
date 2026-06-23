clc;
clear;
close all;

script_dir = fileparts(mfilename('fullpath'));
repo_root = fileparts(fileparts(script_dir));
output_dir = fullfile(repo_root, 'outputs', 'power_maps');
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

scene_filepath_nocell = fullfile(repo_root, 'data', 'scene_models', 'scene1_nocell.stl');
json_no_ris = fullfile(repo_root, 'data', 'power_maps', 'scene1_noris.json');
json_with_ris = fullfile(repo_root, 'data', 'power_maps', 'scene1_area3.json');

BS_loc = [13.2, -7.575, 1.25]';
RIS_loc = [13.2, -8.3, 1.25]';
L = 1.25;
z_height = 1.25;
step_size = 0.5;
map_down = -60;
flag = 1;
% 
% To visualize the residential apartment, select scene2_nocell.stl and the
% corresponding scene2 JSON files from data/power_maps.
% 
% BS_loc = [8.397, 0.721, 0.75]';
% RIS_loc = [8.959, 1.253, 0.75]';
% z_height = 1.6;

disp('Reading JSON data...');
data_no = jsondecode(fileread(json_no_ris));
data_with = jsondecode(fileread(json_with_ris));

x_no = [data_no.x]'; y_no = [data_no.y]'; z_no = [data_no.z]'; p_no = [data_no.power]';
x_with = [data_with.x]'; y_with = [data_with.y]'; z_with = [data_with.z]'; p_with = [data_with.power]';

disp('Reconstructing the power grid...');
X_vec = min([x_no; x_with]) : step_size : max([x_no; x_with]);
Y_vec = min([y_no; y_with]) : step_size : max([y_no; y_with]);

[Xg, Yg] = meshgrid(X_vec, Y_vec);

P_map_no_ris = nan(size(Xg));
Z_map_no_ris = nan(size(Xg));

P_map_with_ris = nan(size(Xg));
Z_map_with_ris = nan(size(Xg));

for i = 1:length(x_no)
    c = round((x_no(i) - X_vec(1)) / step_size) + 1;
    r = round((y_no(i) - Y_vec(1)) / step_size) + 1;
    P_map_no_ris(r, c) = p_no(i);
    Z_map_no_ris(r, c) = z_no(i);
end

for i = 1:length(x_with)
    c = round((x_with(i) - X_vec(1)) / step_size) + 1;
    r = round((y_with(i) - Y_vec(1)) / step_size) + 1;
    P_map_with_ris(r, c) = p_with(i);
    Z_map_with_ris(r, c) = z_with(i);
end

disp('Rendering the 3D scene overlays...');
scene_model = stlread(scene_filepath_nocell);

if flag==1 || flag==3
    ris_rect_x = [RIS_loc(1)-L/2, RIS_loc(1)+L/2, RIS_loc(1)+L/2, RIS_loc(1)-L/2];
    ris_rect_y = [RIS_loc(2), RIS_loc(2), RIS_loc(2), RIS_loc(2)];
    ris_rect_z = [RIS_loc(3)-L/2, RIS_loc(3)-L/2, RIS_loc(3)+L/2, RIS_loc(3)+L/2];
elseif flag==2
    ris_rect_x = [RIS_loc(1), RIS_loc(1), RIS_loc(1), RIS_loc(1)];
    ris_rect_y = [RIS_loc(2)-L/2, RIS_loc(2)+L/2, RIS_loc(2)+L/2, RIS_loc(2)-L/2];
    ris_rect_z = [RIS_loc(3)-L/2, RIS_loc(3)-L/2, RIS_loc(3)+L/2, RIS_loc(3)+L/2];
end

fig1 = figure('Name', '3D Scene: Without RIS', 'Color', 'w', 'Position', [100, 100, 800, 600]);
hold on; axis equal tight; axis off;
view(30, 45);
if ~isempty(scene_model)
    trisurf(scene_model, 'FaceColor', [116/255 4/255 4/255], 'EdgeColor', 'none', ...
            'FaceAlpha', 0.15, 'SpecularStrength', 0.1);
    camlight('headlight'); material('dull');
end
surf(Xg, Yg, Z_map_no_ris, P_map_no_ris, 'EdgeColor', 'none', 'FaceAlpha', 0.85);
shading interp; colormap('jet'); clim([map_down -10]); 

set(gca, 'Position', [0 0 1 1]); 
camzoom(1);

set(fig1, 'PaperUnits', 'inches', 'PaperPosition', [0 0 12 9]);
print(fig1, fullfile(output_dir, 'workplace_power_no_ris.png'), '-dpng', '-r300');


fig2 = figure('Name', '3D Scene: With RIS', 'Color', 'w', 'Position', [820, 100, 800, 600]);
hold on; axis equal tight; axis off;
view(30, 45);
if ~isempty(scene_model)
    trisurf(scene_model, 'FaceColor', [116/255 4/255 4/255], 'EdgeColor', 'none', ...
            'FaceAlpha', 0.15, 'SpecularStrength', 0.1);
    camlight('headlight'); material('dull');
end
surf(Xg, Yg, Z_map_with_ris, P_map_with_ris, 'EdgeColor', 'none', 'FaceAlpha', 0.85);
shading interp; colormap('jet'); clim([map_down -10]); 

set(gca, 'Position', [0 0 1 1]);
camzoom(1);

set(fig2, 'PaperUnits', 'inches', 'PaperPosition', [0 0 12 9]);
% print(fig2, 'picture_show/scene1_power_area2.png', '-dpng', '-r300');


disp('Rendering the standalone color bar...');
fig_cb = figure('Name', 'Standalone Colorbar', 'Color', 'w', 'Position', [400, 400, 800, 200]);
ax = axes('Visible', 'off');
colormap(ax, 'jet');
clim(ax, [map_down -10]);

cb_alone = colorbar(ax, 'Location', 'south'); 
cb_alone.Label.String = 'Power (dBm)';
cb_alone.FontSize = 14;

set(ax, 'Position', [0.1 0.4 0.8 0.3]); 

set(fig_cb, 'PaperUnits', 'inches', 'PaperPosition', [0 0 10 2]);
% print(fig_cb, 'picture_show/scene1_colorbar.png', '-dpng', '-r300');

disp('All plots are complete.');
