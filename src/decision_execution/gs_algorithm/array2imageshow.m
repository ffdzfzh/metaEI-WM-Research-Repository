function  array2imageshow(image_array,num_x,num_y)
image=zeros(num_y,num_x);
index = 1;
 for i= 1 :  num_x
    for j= 1 : num_y
        image(j,i) =  image_array(index);
        index = index + 1;
     end
 end
 
%imshow(image,[]);
colormap(jet)
imagesc(image);
% lambda = 3*10^8/(15.6*10^9);
% num_lam = 240/1000/lambda;
% 
% 
% dis_xlble = linspace(0,num_lam,5);
% dis_xlble =round(dis_xlble,1);
% for i=1:length(dis_xlble)
%     str_dis_xlble{i} = num2str(dis_xlble(i));
% end
% str_num2xlable = linspace(1,40,5);
% haxes = get(h,'parent');
% set(haxes,'xtick',str_num2xlable,'xticklabel',str_dis_xlble)
% 
% dis_ylble = linspace(num_lam,0,5);
% dis_ylble =round(dis_ylble,1);
% for i=1:length(dis_ylble)
%     str_dis_ylble{i} = num2str(dis_ylble(i));
% end
% str_num2ylable =linspace(1,40,5);
% haxes = get(h,'parent');
% set(haxes,'ytick',str_num2ylable,'yticklabel',str_dis_ylble,'FontSize',8)
% 
% colorbar

% figure
% contour(image); 
end

