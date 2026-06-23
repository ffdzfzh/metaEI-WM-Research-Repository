clc;
clear;
close all;

script_dir = fileparts(mfilename('fullpath'));
repo_root = fileparts(fileparts(script_dir));
output_dir = fullfile(repo_root, 'outputs', 'power_maps');
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end
scene_filepath = fullfile(repo_root, 'data', 'scene_models', 'scene3_2.stl');
json_no_ris = fullfile(repo_root, 'data', 'power_maps', 'scene3_noris.json');
json_with_ris = fullfile(repo_root, 'data', 'power_maps', 'scene3_area1.json');

BS_loc = [1, 0.5, 1.2]';
RIS_loc = [1.75, 0.1, 1.2]';

f_c = 5e9;
lambda = 3e8 / f_c;
d_RIS = lambda / 2;
RIS_dim = [16, 16];
W = RIS_dim(2) * d_RIS;
H = RIS_dim(1) * d_RIS;

step_size = 0.1;

max_z_jump = 0.4; 

disp('Reading JSON data...');
data_no = jsondecode(fileread(json_no_ris));
data_with = jsondecode(fileread(json_with_ris));

x_no = [data_no.x]'; y_no = [data_no.y]'; z_no = [data_no.z]' - 0.4; p_no = [data_no.power]';
x_with = [data_with.x]'; y_with = [data_with.y]'; z_with = [data_with.z]' - 0.4; p_with = [data_with.power]';

disp('Reconstructing the power grid...');
min_x = min([x_no; x_with]);
min_y = min([y_no; y_with]);

c_idx_no = round((x_no - min_x) / step_size) + 1;
r_idx_no = round((y_no - min_y) / step_size) + 1;
c_idx_with = round((x_with - min_x) / step_size) + 1;
r_idx_with = round((y_with - min_y) / step_size) + 1;

max_c = max([c_idx_no; c_idx_with]);
max_r = max([r_idx_no; r_idx_with]);

X_vec = min_x + (0 : max_c - 1) * step_size;
Y_vec = min_y + (0 : max_r - 1) * step_size;
[Xg, Yg] = meshgrid(X_vec, Y_vec);

P_map_no_ris = nan(max_r, max_c);
Z_map_no_ris = nan(max_r, max_c);
P_map_with_ris = nan(max_r, max_c);
Z_map_with_ris = nan(max_r, max_c);

for i = 1:length(x_no)
    Z_map_no_ris(r_idx_no(i), c_idx_no(i)) = z_no(i);
    P_map_no_ris(r_idx_no(i), c_idx_no(i)) = p_no(i);
end

for i = 1:length(x_with)
    Z_map_with_ris(r_idx_with(i), c_idx_with(i)) = z_with(i);
    P_map_with_ris(r_idx_with(i), c_idx_with(i)) = p_with(i);
end

disp('Rendering the 3D scene overlays...');
scene_model = stlread(scene_filepath);
ris_rect_x = [RIS_loc(1)-W/2, RIS_loc(1)+W/2, RIS_loc(1)+W/2, RIS_loc(1)-W/2];
ris_rect_y = [RIS_loc(2), RIS_loc(2), RIS_loc(2), RIS_loc(2)];
ris_rect_z = [RIS_loc(3)-H/2, RIS_loc(3)-H/2, RIS_loc(3)+H/2, RIS_loc(3)+H/2];

fig1 = figure('Name', '3D Scene: Without RIS', 'Color', 'w', 'Position', [100, 100, 800, 600]);
hold on; axis equal tight; axis off;
view(45, 30);
if ~isempty(scene_model)
    trisurf(scene_model, 'FaceColor', [116/255 4/255 4/255], 'EdgeColor', 'none', ...
            'FaceAlpha', 0.15, 'SpecularStrength', 0.1);
    camlight('headlight'); material('dull');
end
plot_split_surf(Xg, Yg, Z_map_no_ris, Z_map_no_ris, P_map_no_ris, max_z_jump);
colormap('jet'); clim([-80 -30]); 

set(gca, 'Position', [0 0 1 1]); 
camzoom(1);
set(fig1, 'PaperUnits', 'inches', 'PaperPosition', [0 0 12 9]); % 12*300=3600, 9*300=2700
print(fig1, fullfile(output_dir, 'corridor_power_no_ris.png'), '-dpng', '-r300');


fig2 = figure('Name', '3D Scene: With RIS', 'Color', 'w', 'Position', [820, 100, 800, 600]);
hold on; axis equal tight; axis off;
view(45, 30);
if ~isempty(scene_model)
    trisurf(scene_model, 'FaceColor', [116/255 4/255 4/255], 'EdgeColor', 'none', ...
            'FaceAlpha', 0.15, 'SpecularStrength', 0.1);
    camlight('headlight'); material('dull');
end
plot_split_surf(Xg, Yg, Z_map_with_ris, Z_map_with_ris, P_map_with_ris, max_z_jump);
colormap('jet'); clim([-80 -30]); 

set(gca, 'Position', [0 0 1 1]); 
camzoom(1);
set(fig2, 'PaperUnits', 'inches', 'PaperPosition', [0 0 12 9]);
print(fig2, fullfile(output_dir, 'corridor_power_with_ris.png'), '-dpng', '-r300');

disp('Rendering the standalone color bar...');
fig_cb = figure('Name', 'Standalone Colorbar', 'Color', 'w', 'Position', [400, 400, 800, 200]);
ax = axes('Visible', 'off'); 
colormap(ax, 'jet');
clim(ax, [-80 -30]);

cb_alone = colorbar(ax, 'Location', 'south'); 
cb_alone.Label.String = 'Power (dBm)';
cb_alone.FontSize = 14; 

set(ax, 'Position', [0.1 0.4 0.8 0.3]); 
set(fig_cb, 'PaperUnits', 'inches', 'PaperPosition', [0 0 10 2]);
print(fig_cb, fullfile(output_dir, 'corridor_colorbar.png'), '-dpng', '-r300');

disp('All plots are complete.');


function p = plot_split_surf(X, Y, Z_logic, Z_draw, C, max_jump)
    [nr, nc] = size(X);
    V = [X(:), Y(:), Z_draw(:)];
    
    [R, C_idx] = ndgrid(1:nr-1, 1:nc-1);
    idx1 = R + (C_idx-1)*nr;
    idx2 = R+1 + (C_idx-1)*nr;
    idx3 = R+1 + C_idx*nr;
    idx4 = R + C_idx*nr;
    F = [idx1(:), idx2(:), idx3(:), idx4(:)];
    
    v1_z = Z_logic(idx1(:));
    v2_z = Z_logic(idx2(:));
    v3_z = Z_logic(idx3(:));
    v4_z = Z_logic(idx4(:));
    
    valid_z = ~isnan(v1_z) & ~isnan(v2_z) & ~isnan(v3_z) & ~isnan(v4_z);
    
    max_z = max([v1_z, v2_z, v3_z, v4_z], [], 2);
    min_z = min([v1_z, v2_z, v3_z, v4_z], [], 2);
    valid_faces = valid_z & ((max_z - min_z) <= max_jump);
    
    F = F(valid_faces, :);
    
    p = patch('Vertices', V, 'Faces', F, 'FaceVertexCData', C(:), ...
          'FaceColor', 'interp', 'EdgeColor', 'none', 'FaceAlpha', 0.85);
end
