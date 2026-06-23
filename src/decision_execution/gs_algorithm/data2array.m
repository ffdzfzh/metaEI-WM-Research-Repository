function  array=data2array(image_array,num_x,num_y,dis)
array=zeros(num_y,num_x);
index = 1;

  for i= 1 :  num_x
    for j= 1 : num_y
        if dis == 0
            array(j,i) =  image_array(index);
        elseif dis == 1
             array(i,j) =  image_array(index);
        end
        index = index + 1;
     end
 end
 
end
